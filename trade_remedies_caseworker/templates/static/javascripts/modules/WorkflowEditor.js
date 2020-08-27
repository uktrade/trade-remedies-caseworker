define([
  "modules/helpers",
  "modules/popUps",
  "modules/moment.min",
  "modules/Events",
], function (helpers, popups, moment, Events) {
  var schema_version = "1.1"; // Indicates if the workflow needs cleaning/updating

  var tpNodeLine = _.template(
    '\
	 	<li class="edit-item" data-key="<%=action.key%>">\
			<div class="node-container">\
				 		<% if(action.children) { %><a class="expander"></a><% } %>\
				<!-- <span class="pull-right"><%= state %></span>-->\
			    <div class="pull-right action-container">\
    				<a class="icon icon-bin pull-right delete" title="Remove"></a>\
    				<a class="icon icon-down pull-right down"  title="Move down"></a>\
    				<a class="icon icon-up pull-right up"  title="Move up"></a>\
    			</div>\
    			<% if(action.response_type) { %>\
					<div class="type-label"><%= (action.response_type || {name:"UNSET-TASK"}).name %></div>\
				<% } %>\
    			<span><a class="edit"><%= action.label || "&nbsp;" %></a>\
				<% if(!action.children && (!action.response_type)) { %>\
					<a class="link child" title="Add child item">&lt; add child &gt;</a>\
				<% } %>\
				</span>\
    		</div>\
    		<%=sub %>\
    	</li>\
	'
  );

  var tpChooseType = _.template(
    '\
		<form action="#"  class="workflow choose-type">\
			<h2 class="heading-medium">Select node type</h2>\
			<div class="form-group inline">\
				<label class="form-label" for="item-key">Node type</label>\
				<select id="item-node-type" name="node_type" class="form-control">\
					<% print(f.renderOptions(nodeTypes)); %>\
				</select>\
			</div>\
			<div class="button-container">\
				<button type="button" class="button button-blue compact" value="btn-save">Ok</button>\
				<button type="button" class="button button-grey pull-right compact dlg-close" value="btn-cancel">Cancel</button>\
			</div>\
		</form>\
		'
  );

  var tpEditNode = _.template(
    '\
		<form action="#" class="workflow node-edit">\
			<h2 class="heading-medium"><%=node_type ? "Create" : "Edit"%> <%=node_type || (node.response_type ? "task" : "action") %></h2>\
			<div class="form-group inline">\
			<label class="form-label" for="item-key">Key</label>\
			<input type="text" id="item-key" class="form-control" name="key" value="<%=node.key%>">\
		</div>\
		<div class="form-group inline">\
			<label class="form-label" for="item-label">Label</label>\
			<textarea id="item-label" class="form-control" name="label"><%=node.label%></textarea>\
		</div>\
		<div class="form-group inline">\
			<label class="form-label" for="item-required">Required</label>\
			<div class="multiple-choice">\
				<input id="required" type="checkbox" name="required" value="true" <% if(node.required) { %>checked="checked"<% } %>>\
				<label for="required"></label>\
			</div>\
		</div>\
		<div class="form-group inline">\
			<label class="form-label" for="item-active">Active</label>\
			<div class="multiple-choice">\
				<input id="active" type="checkbox" name="active" value="true"<% if(node.active) { %>checked="checked"<% } %>>\
				<label for="active"></label>\
			</div>\
		</div>\
		<% if (node.response_type || node_type=="task") { %>\
		<div class="form-group inline">\
			<label class="form-label" for="item-response-type">Response type</label>\
			<select id="item-response-type" name="response_type" class="form-control" value="<%=(node.response_type || {}).id%>">\
			<% print(f.renderOptions(responseTypes, (node.response_type || {}).name)); %>\
			</select>\
		</div>\
		<% } %>\
		<div class="form-group inline">\
			<label class="form-label" for="item-timegate">Time gate</label>\
			<input type="text" id="item-timegate" name="time_gate" class="form-control" value="<%=node.time_gate%>">\
		</div>\
		<div class="form-group inline">\
			<label class="form-label" for="item-permission">Permission</label>\
			<input type="text" id="item-permission" name="permission" class="form-control" value="<%=node.permission%>">\
		</div>\
		<div class="form-group inline">\
			<label class="form-label" for="item-outcome">Outcome</label>\
			<textarea id="item-outcome" class="form-control" name="outcome_spec" rows="10"><%=JSON.stringify(node.outcome_spec, null, 4)%></textarea>\
		</div>\
		<div class="form-group hidden">\
		<% for( idx in (node.outcome_spec || [])) { %>\
			<% var outcome = node.outcome_spec[idx]; %>\
			<%=outcome.type%>\
			<% for( key in (outcome.spec[0])) { %>\
				<%=key %>:<%=outcome.spec[0][key]%>\
				<% } %>\
			<% } %>\
		</div>\
		<div class="button-container">\
			<button class="button button-blue compact" value="btn-save">Save</button>\
			<button class="button button-grey pull-right compact dlg-close" value="btn-cancel">Cancel</button>\
		</div>\
		</form>\
		'
  );

  var tpStateLine = _.template(
    '<tr data-key="<%=key%>">\
		<td><%=key%></td>\
		<td><div class="in-place-edit value" data-attach="EditInPlace2" data-model="state" data-id="<%=key%>" data-name="<%=key%>"><%=value ? value : "&lt;empty&gt;" %></div></td>\
		<td sortVal="<%=(due ? formatDate(due,"YYYY-MM-DDTHH/mm/ss") : "") %>"><span class="nobreak"><%=(due ? formatDate(due) : "") %></span></td>\
		<td><%=node && node.response_type && node.response_type.name %></td>\
		</tr>'
  );

  var tpOption = _.template(
    '<option value="<%=option.id || option.name%>" <% if(selected) { %>selected=selected<% } %> ><%=option.name%></option>'
  );

  var form = $("form.dd-form");
  var editMode = localStorage.config == "onnode";

  var menu; // the menu element
  var menuShowing;

  function renderChildren(node) {
    var out = "";
    var node_type;
    _.each(
      node.children,
      function (child) {
        out += tpNodeLine({
          action: child,
          sub: child.children && renderLevel.call(this, child, true),
          state: this.state[child.key],
        });
        this.keyMap[child.key] = child;
        this.parentMap[child.key] = node;
        node_type = node_type || (child.response_type ? "Task" : "Action");
      },
      this
    );
    out +=
      '<a href="javaScript:void(0);" class="link create">Add ' +
      (node_type || {}) +
      "</a>";
    return out;
  }

  function renderLevel(node, hide) {
    // Render the children of a node
    this.keyMap[node.key] = node;
    var out = '<ul class="action-list ' + (hide ? "js-hidden" : "") + '">';
    out += renderChildren.call(this, node);
    out += "</ul>";
    return out;
  }

  function onClick(evt) {
    var self = this;
    var target = $(evt.target);
    var editItem = target.closest(".edit-item");
    var itemKey = editItem.attr("data-key");
    var item = editItem && this.keyMap[itemKey];

    // outer container for refresh
    function refreshParent() {
      outer = editItem.parent().closest(".edit-item");
      parent = self.parentMap[itemKey];
      outer.children("ul").html(renderChildren.call(self, parent));
    }

    if (target.is(".edit")) {
      this.editItem(item).then(refreshParent);
    }
    if (target.is(".delete")) {
      this.deleteItem(item, this.parentMap[itemKey]);
      refreshParent();
    }
    if (target.is(".create")) {
      item = item || this.keyMap["root"];
      this.createItemIn(item).then(function () {
        // refresh this node's children
        editItem.children("ul").html(renderChildren.call(self, item));
      });
    }
    if (target.is(".child")) {
      this.createItemIn(item).then(function () {
        refreshParent();
      });
    }
    if (target.is(".up,.down")) {
      this.shift(item, this.parentMap[itemKey], target.is(".up") ? -1 : 1);
      refreshParent();
    }
    if (target.is(".expander")) {
      editItem.toggleClass("expanded");
    }
    if (target.is("[data-tab]")) {
      evt.preventDefault();
      var tab = target.attr("data-tab");
      $(".tab-page.active").removeClass("active");
      $(".tab-page." + tab).addClass("active");
    }
  }

  function createMap(list, key) {
    var out = {};
    key = key || "id";
    _.each(list, function (item) {
      out[item[key]] = item;
    });
    return out;
  }

  function renderOptions(list, selected) {
    var out = "";
    _.each(list, function (item) {
      out += tpOption({ option: item, selected: selected == item.name });
    });
    return out;
  }

  function constructor(el, workflow, state) {
    this.el = el;
    this.workarea = this.el.find(".workflow-page");
    this.statearea = this.el.find(".state-page");
    this.saveButton = this.el.find("button[value=btn-save]");
    this.saveButton.on("click", _.bind(saveWorkflow, this));
    this.el
      .find("button[value=btn-dump]")
      .on("click", _.bind(dumpWorkflow, this));
    this.el
      .find("button[value=btn-check]")
      .on("click", _.bind(cleanWorkflow, this));
    el.on("click", _.bind(onClick, this));
    this.workflow = workflow;
    this.state = state;
    this.keyMap = {};
    this.parentMap = {};
    this.nodeTypeMap = createMap(nodeTypes);
    this.responseTypeMap = createMap(responseTypes);
    this.responseTypeNameMap = createMap(responseTypes, "name");
    new Events().listen("In-place-edit-save", _.bind(onEditSave, this));
    this.render();
  }

  function onEditSave(details) {
    this.state = details.result.workflow_state;
    this.updateState();
  }

  function cleanNode(node) {
    var self = this;
    delete node.parent;
    delete node.order;
    delete node.value;
    delete node.due_date;
    delete node.id;
    // node.active = true;  we are setting this explicitly so don't override

    if (node.children && node.children.length) {
      // It's an action so clean off non-action stuff
      delete node.response_type;
    } else {
      node.response_type =
        self.responseTypeNameMap[
          node.response_type && node.response_type.name
        ] || responseTypes[3]; //default to checkbox
    }
    // Make the time_gate a number if it can be
    if (typeof node.time_gate == "string") {
      node.time_gate = parseInt(node.time_gate, 10) || null;
    }
    // Check the outcome
    _.each(node.outcome_spec || [], function (outcome) {
      _.each(outcome.spec, function (spec) {
        //console.log('Spec' ,spec);
        _.each(spec, function (inner) {
          if (inner.key) {
            _.each(_.isArray(inner.key) ? inner.key : [inner.key], function (
              key
            ) {
              if (!self.keyMap[key]) {
                self.report =
                  (self.report || "") +
                  '<li>Unmatched key:"' +
                  key +
                  '" in outcome ' +
                  node.key +
                  "</li>";
              }
            });
          }
        });
      });
    });
  }

  function cleanUp(parent) {
    var self = this;
    _.each(parent.children, function (node) {
      cleanNode.call(self, node);
      if (node.children) {
        cleanUp.call(self, node);
      }
    });
  }

  function cleanWorkflow() {
    this.report = "";

    if (this.workflow.schema_version != schema_version) {
      this.workflow.schema_version = schema_version;
    }

    cleanUp.call(this, { children: this.workflow.root });
    if (this.report) {
      popups.error("<ul>" + this.report + "</ul>");
    } else {
      popups.alert("All hunky dory!");
    }
  }

  function dumpWorkflow() {
    var txt = JSON.stringify({ root: this.workflow.root }, null, 4);
    popups.alert("<textarea>" + txt + "</textarea>", "Ready to cut'n'paste");
  }

  function saveWorkflow() {
    var data = {
      workflow: JSON.stringify({ root: this.workflow.root }),
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
    var url = location.href;
    $.ajax({
      url: url,
      method: "post",
      dataType: "json",
      data: data,
    }).then(
      function (response) {
        popups.alert("Workflow saved");
      },
      function (response) {
        popups.error("Save failed");
      }
    );
  }

  var nodeTypes = [
    { id: "action", name: "Action" },
    { id: "task", name: "Task" },
  ];

  var responseTypes = [
    { name: "Yes/No", key: "YESNO" },
    { name: "Free Text", key: "TEXT" },
    { name: "Text area", key: "TEXTAREA" },
    { name: "Selection", key: "SELECT" },
    { name: "Checkbox/NA", key: "CHECKBOX_NA" },
    { name: "Checkbox", key: "CHECKBOX" },
    { name: "NoteSection", key: "NOTES" },
    { name: "Yes/No/NA", key: "YESNO_NA" },
    { name: "Timer", key: "TIMER" },
    { name: "Label", key: "LABEL" },
    { name: "Date", key: "DATE" },
    { name: "Hidden", key: "HIDDEN" },
  ];

  function updateNode(node, data) {
    // Copy values from data into node
    var map = helpers.unMap(data);
    var nodeRef = this.keyMap[map.key];
    map.key = (map.key || "").toUpperCase();
    if (!map.key) {
      popups.error("Key is mandatory");
      return;
    }
    if (nodeRef && nodeRef != node) {
      popups.error("Key (" + map.key + ") is not unique");
      return;
    }
    if (!nodeRef) {
      delete this.keyMap[node.key]; // if the key has changed, this removes the old key so that map checks still work.
    }
    if (!map.label) {
      popups.error("Label is mandatory");
      return;
    }
    delete node.required;
    delete node.active;
    delete node.permission;
    _.each(
      map,
      function (value, key) {
        if (key == "response_type") {
          value = this.responseTypeNameMap[value] || null;
        }
        if (key == "outcome_spec" && value) {
          value = JSON.parse(value);
        }
        if (key in { required: 1, active: 1 }) {
          value = value == "true";
        }
        node[key] = value;
      },
      this
    );
    return true;
  }

  function chooseType() {
    var self = this;
    return new Promise(function (resolve, reject) {
      require(["modules/Lightbox"], function (Lightbox) {
        var lb = new Lightbox({
          content: tpChooseType({
            nodeTypes: nodeTypes,
            f: {
              renderOptions: renderOptions,
            },
          }),
        });
        lb.getContainer()
          .find('button[value="btn-save"]')
          .on("click", function () {
            var data = lb.getContainer().find("form").serializeArray();
            resolve(self.nodeTypeMap[helpers.unMap(data).node_type]);
            lb.close();
          });
      });
    });
  }

  function editNode(node, node_type) {
    var self = this;
    return new Promise(function (resolve, reject) {
      require(["modules/Lightbox"], function (Lightbox) {
        var content = tpEditNode({
          node: node,
          f: {
            renderOptions: renderOptions,
          },
          responseTypes: responseTypes,
          nodeTypes: nodeTypes,
          node_type: node_type,
        });
        var lb = new Lightbox({
          content: content,
        });
        lb.getContainer()
          .find("button")
          .on("click", function (evt) {
            evt.preventDefault();
            var form = lb.getContainer().find("form");
            if ($(evt.target).val() == "btn-save") {
              var result = updateNode.call(self, node, form.serializeArray());
              if (result) {
                lb.close();
                resolve();
              }
            } else {
              reject();
            }
          });
      });
    });
  }

  constructor.prototype = {
    render: function () {
      this.workarea.html(
        renderLevel.call(this, { key: "root", children: this.workflow.root })
      );
      this.showState();
      this.statearea.attachWidgets();
    },
    editItem: function (node) {
      var self = this;
      return new Promise(function (resolve) {
        editNode.call(self, node).then(resolve);
      });
    },
    deleteItem: function (node, parent) {
      var self = this;
      var idx = parent.children.indexOf(node);
      parent.children.splice(idx, 1);
      if (!parent.children.length) {
        delete parent.children;
      }
    },
    shift: function (node, parent, direction) {
      var self = this;
      var idx = parent.children.indexOf(node);
      var newIdx = idx + direction;
      if (newIdx >= 0 && newIdx < parent.children.length) {
        parent.children.splice(idx, 1);
        parent.children.splice(newIdx, 0, node);
      }
    },
    formatDate(date, format) {
      return moment(date).format(format || "MMM Do YYYY");
    },
    showState() {
      // display all the state keys that don't correspond to actions
      var self = this;
      var html =
        '<table class="sortable" data-attach="TableSort"><thead><tr>\
						<th><span class="pull-left">Key</span></th>\
						<th><span class="pull-left">Value</span></th>\
						<th><span class="pull-left">Due</span></th>\
						<th><span class="pull-left">Type</span></th>\
						</thead><tbody></tbody></table>';
      /*			_.each(self.state, function(value, key) {
				if(!_.isArray(value)) {
					value = [value, null];
				}
				out += tpStateLine({key:key, value:value[0], due: value[1], formatDate: self.formatDate , node: self.keyMap[key]});
			});*/
      this.statearea.html(html);
      this.updateState();
    },
    updateState: function () {
      var self = this;
      var table = this.statearea.find("table tbody");
      var tmpVal = _.template('<%=value ? value : "&lt;empty&gt;" %>');
      this.stateElMap = this.stateElMap || {};
      _.each(this.state, function (value, key) {
        var row = self.stateElMap[key];
        if (!row) {
          row = $(
            tpStateLine({
              key: key,
              value: value[0],
              due: value[1],
              formatDate: self.formatDate,
              node: self.keyMap[key],
            })
          );
          table.append(row);
        }
        var state = value && value[0];
        if (state && typeof state == "object") {
          state = JSON.stringify(state);
        }
        var txt = tmpVal({ value: state });
        row.find("div.value").html(txt);
      });
      /*


			this.statearea.find('tr[data-key]').each(function() {
				var row = $(this);
				var key = row.attr('data-key');
				state = (self.state[key] || [])[0];
				if(state && typeof(state) == 'object') {
					state=JSON.stringify(state);
				}
				var txt = tmpVal({value: state});
				row.find('span.value').html(txt);
			})
*/
    },
    createItemIn: function (parent) {
      var self = this;

      return new Promise(function (resolve) {
        var node = {};
        function completeEditNode(node_type) {
          if (node_type == "task") {
            node.required = true;
          }
          editNode.call(self, node, node_type).then(function () {
            (parent.children = parent.children || []).push(node);
            resolve();
          });
        }

        if (parent.children && parent.children.length) {
          var rt = parent.children[0].response_type;
          var node_type = rt && rt.name ? "task" : "action";
        }

        var idx = 1;
        var key = parent["key"] + "_" + ("" + idx).pad(3);
        while (self.keyMap[key]) {
          idx++;
          key = parent["key"] + "_" + ("" + idx).pad(3);
        }
        node["key"] = key.toUpperCase();
        node["active"] = true;
        if (!node_type) {
          chooseType.call(self).then(function (nodeType) {
            completeEditNode(nodeType.id);
          });
        } else {
          completeEditNode(node_type);
        }
      });
    },
  };

  return constructor;
});
