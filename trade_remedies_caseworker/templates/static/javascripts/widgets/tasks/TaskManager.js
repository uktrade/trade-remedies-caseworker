define([
  "modules/helpers",
  "modules/Events",
  "widgets/ContentTypeLink",
  "widgets/tasks/TaskViewer",
  "widgets/tasks/TaskList",
  "modules/overlay",
], function (helpers, Events, ContentTypeLink, TaskViewer, TaskList, overlay) {
  "use strict";

  var cachePollPeriod = 60 * 1000;

  var templateStrings = {
    outer: `
        <div>
            <div class="task-top-panel">
                <% if(window.dit.caseId) { %>
                    <div class="counts">
                        <div class="task-count" data-key="own">Your tasks<span class="count circular-badge small">&nbsp;</span></div>
                        <div class="task-count" data-key="page">Page tasks<span class="count circular-badge small">&nbsp;</span></div>
                        <button class="link add-task no-debounce">+ New task</button>
                        <!-- <div class="pull-right expander link -icon -icon-down" data-attach="ExpandCollapse" data-slave="#tasklist-container" data-storagekey="filter-expand" ></div> -->
                        <a href="javascript:void(0)" class="link bold menu-icon" data-attach="menuExpand"></a>
                        <span class="function-menu">
                            <div>
                                <ul>
                                    <li><button type="button" class="dlg-close no-debounce" name="btn-action" value="viewerMode">Slide viewer</button></li>
                                    <li><button type="button" class="dlg-close no-debounce" name="btn-action" value="leftPanel">Task panel side</button></li>
                                </ul>
                            </div>
                        </span>
                    </div>
                <% } %>
                <div class="not-expand-section" style="overflow:hidden;max-height:42px;">
                    <div class="view-selector pull-left">
                        <% var fnMode = function(value) {return (obj.settings.listMode == value) ? 'checked="checked"' : ''} %>
                        <label title="List view"><input type="radio" name="listMode" value="table" <%=fnMode('table')%> ><i class="icon icon-table-view"></i></label>
                        <label title="Card view"><input type="radio" name="listMode" value="card" <%=fnMode('card')%>><i class="icon icon-card-view"></i></label>
                        <label title="Calendar view"><input type="radio" name="listMode" value="calendar" <%=fnMode('calendar')%>><i  class="icon icon-calendar-sm"></i></label>
                        <% if(obj.self.mode=='my-tasks') { %>
                            <label title="Non-working days"><input type="radio" name="listMode" value="nwds" <%=fnMode('nwds')%>><i class="icon icon-holiday"></i></label>
                        <% } %>
                    </div>
                    <div class="task-filters">
                        <div class="pull-left margin-left-1">
                          <div class="assignee-filter pull-left margin-right-1">
                            <% if(obj.self.mode=='my-tasks') { %>
                            <input type="checkbox" class="hidden" checked="true" name="assignee_id" value="<%=window.dit.user_id%>">
                            <% } %>
                          </div>
                          <% if(obj.self.mode=='my-tasks') { %>
                            <div class="case-filter pull-left margin-right-1"></div>
                          <% } %>
                        </div>
                        <div class="multiple-choice tiny pull-right include-done-tasks-container">
                            <input id="include-done-checkbox" name="status" value="done" data-combination="not" type="checkbox" data-direction="off">
                            <label for="include-done-checkbox" class="form-label">
                                Include done
                            </label>
                        </div>
                        </div>
                    </div>

                </div>
            </div>
            <div id="tasklist-container" class="expand-slave">
                <div class="tasklist" data-attach="ScrollShadow"></div>
                <div class="task-viewer-container"></div>
            </div>
        </div>
        `,
    userBadge: `
            <div title="<%=obj.name || 'Unassigned'%>" class="circular-badge small" style="background:<%=obj.colour || 'black'%>"><%=obj.initials || '?'%></div>
        `,
    userSelect: `
            <label>
              <div class="multiple-choice tiny pull-left">
                <input name="assignee_id" value="<%=obj.id || 'null'%>" data-combination="or" type="checkbox">
                <label></label>
              </div>
              <div title="<%=obj.name || 'Unassigned'%>" class="circular-badge small" style="background:<%=obj.colour || 'black'%>"><%=obj.initials || '?'%></div>
              <span class="name"><%=obj.name || 'Unassigned' %></span>
            </label>
        `,
    assigneeFilter: `
      <div class="assignee-dropdown-container">
          <a href="javascript:void(0)" class="show-assignees-link">Filter by team member</a>
          <a href="javascript:void(0)" class="clear-assignee-filters-button margin-left-1">Clear filters</a>
          <div class="assignees" style="position:relative;">
              <div class="user-select-dropdown">
                  <% for(var idx=0;idx<=obj.users.length;idx++) { 
                      var user = obj.users[idx] || {};
                      %>
                      <div class="user-select-dropdown__item">
                          <%= obj.self.templates.userSelect(user) %>
                      </div>
                  <% } %>
              </div>
          </div>
      </div>
        `,
  };

  var defaultSettings = {
    listMode: "table",
  };

  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.mode = el.attr("data-mode");
    this.viewerMode = el.attr("data-viewer-mode");

    window.helpers = helpers;
    this.settings = _.extend(
      defaultSettings,
      JSON.parse(window.localStorage["tasklist_settings"] || "{}")
    );
    // bodge to prevent NWD list being selected in case view
    if (this.mode != "my-tasks" && this.settings.listMode == "nwds") {
      this.settings.listMode = "table";
    }
    this.activeFilters = JSON.parse(
      window.localStorage["tasklist_filters"] || "{}"
    );
    // initialize the templates
    this.templates = {};
    _.each(
      templateStrings,
      function (str, key) {
        this.templates[key] = _.template(str, { variable: "obj" });
      },
      this
    );
    this.el
      .html(this.templates.outer({ settings: this.settings, self: this }))
      .attachWidgets();
    if (this.mode != "my-tasks") {
      this.renderAssigneeFilter();
    }

    _.bindAll(
      this,
      "onHashChange",
      "onFilterChange",
      "onModeChange",
      "checkCache",
      "onActivateChange",
      "onTasksUpdated",
      "onTablesort",
      "onTopPanelResize"
    );
    $(window).on("hashchange", this.onHashChange);
    this.taskTopPanel = this.el.find(".task-top-panel");
    $(window).on("resize", this.onTopPanelResize);
    this.modeSelector = this.el.find(".view-selector");
    this.modeSelector.on("change", this.onModeChange);
    // initialize the other components
    this.taskViewer = new TaskViewer(
      this,
      this.viewerMode != "popup" ? this.el.find(".task-viewer-container") : null
    );
    this.taskList = new TaskList(this, this.el);
    this.el.on("click", _.bind(onElementClick, this));
    this.$gridContainer = this.el.find(".tasklist");
    this.$filters = this.el.find(".task-filters");
    this.$filters.on("change", this.onFilterChange);

    // Fire the filter change to generate a list of active filters
    this.onFilterChange();
    new Events().listen("tasks_updated", this.onTasksUpdated);
    new Events().listen("tablesort", this.onTablesort);
    new Events().listen("panel-collapse", this.onActivateChange);
    this.updateMenu();
    this.checkCache();
    this.onActivateChange(); // will actually render things
    this.onTopPanelResize();
  };
  var bounceContainer;

  function dinosaurClick(evt) {
    // Not used as yet - testing running the rest of the site without doing any real page-transitions
    // It works - but really needs to set a hash to recover to the correct page on a page refesh
    var target = $(evt.target);
    var aTag = target.closest("a");
    if (aTag.length) {
      evt.preventDefault();
      $.ajax({
        url: aTag.attr("href"),
        method: "get",
      }).then(function (result) {
        var page = $(result);
        var content = page.find("#panel-left");
        var old = $("#panel-left");
        old.html(content.html()).attachWidgets();
      });
    }
  }

  function dismissAssigneeDropdown(e) {
    var targetParent = $(e.target).parents(".assignee-dropdown-container")
      .length;
    if (!targetParent) {
      setAssigneeDropdownVisibility(false);
      stopListeningForDropdownDismiss();
    }
  }

  function listenForAssigneeDropdownDismiss() {
    //Listen to click events on the whole page so we can dismiss the assignee dropdown
    $(document).on("click", dismissAssigneeDropdown);
  }

  function stopListeningForDropdownDismiss() {
    $(document).off("click", dismissAssigneeDropdown);
  }

  function toggleAssigneeDropdown() {
    const $container = $(".assignee-dropdown-container");

    if ($container.hasClass("show-dropdown")) {
      setAssigneeDropdownVisibility(false);
      stopListeningForDropdownDismiss();
    } else {
      $container.addClass("show-dropdown");
      listenForAssigneeDropdownDismiss();
    }
  }

  function setAssigneeDropdownVisibility(visible) {
    if (!visible) $(".user-select-dropdown").scrollTop(0);
    $(".assignee-dropdown-container").toggleClass("show-dropdown", visible);
  }

  function onElementClick(evt) {
    // a click on the trigger element that the manager is attached to
    var self = this;
    var $filter;
    var $target = $(evt.target);
    if ($target.hasClass("add-task")) {
      this.taskViewer.createTask();
    }
    if ($target.hasClass("add-nwd")) {
      this.taskViewer.createNwd();
    }
    if ($target.hasClass("show-assignees-link")) {
      evt.stopPropagation();
      toggleAssigneeDropdown($target);
    }

    if ($target.hasClass("clear-assignee-filters-button")) {
      self.$filters.find('input[name="assignee_id"]').each(function (idx, el) {
        $(el).prop("checked", false);
      });
      this.onFilterChange(evt);
      setAssigneeDropdownVisibility(false);
    }

    // click on task in task list
    var row = $target.closest("tr, .task-card");
    var taskId = row.attr("data-id");
    if (taskId) {
      self.taskViewer.getTask(taskId);
      row.closest("table").find("tr.selected").removeClass("selected");
      row.addClass("selected");
    }
    // filter selectors
    if (($filter = $target.closest(".task-count")).length) {
      var filterKey = $filter.attr("data-key");
      if (this.activeFilters[filterKey]) {
        delete this.activeFilters[filterKey];
        $filter.removeClass("selected");
      } else {
        this.activeFilters[filterKey] = true;
        $filter.addClass("selected");
      }
      window.localStorage["tasklist_filters"] = JSON.stringify(
        this.activeFilters
      );
      this.renderTaskList();
    }

    if ($target.val() == "viewerMode") {
      this.saveSettings({
        viewerMode: this.settings.viewerMode == "slide" ? "bottom" : "slide",
      });
      this.updateMenu();
    }
    if ($target.val() == "leftPanel") {
      var val = GOVUK.getCookie("panel_side");
      val = val == "left" ? "right" : "left";
      GOVUK.cookie("panel_side", val, { days: 30 });
      window.location.reload();
    }
  }

  constructor.prototype = {
    setClearFiltersVisibility(visible) {
      $(".clear-assignee-filters-button", this.el).toggleClass(
        "visible",
        visible
      );
    },

    onTablesort: function (data) {
      var sorter = data.self;
      this.settings.sort = {
        colIndex: data.colIndex,
        direction: data.direction,
      };
      window.localStorage["tasklist_settings"] = JSON.stringify(this.settings);
    },

    onTasksUpdated: function () {
      if (this.active) {
        this.renderTaskList();
      }
    },

    onActivateChange: function () {
      var self = this;
      var active = !this.el.closest(".panel-collapsed").length;
      if (active != this.active) {
        this.active = active;
        if (active) {
          var viewingTask = window.localStorage["viewing_task"];
          if (viewingTask && this.viewerMode != "popup") {
            self.taskViewer.getTask(viewingTask, true).then(function () {
              self.renderTaskList();
            });
          } else {
            self.renderTaskList();
          }
        }
      }
    },

    onTopPanelResize: function () {
      this.taskListContainer =
        this.taskListContainer || this.el.find("#tasklist-container");
      this.taskListContainer.css({ top: this.taskTopPanel.height() + "px" });
    },

    onHashChange: function () {
      this.renderTaskList();
    },

    onFilterChange: function (evt) {
      var self = this;
      var showClearFilterButton = false;
      evt && evt.stopPropagation();
      self.sourceFilters = [];
      this.$filters.find("input").each(function () {
        var $el = $(this);
        var field = $el.attr("name");
        var direction = $el.attr("data-direction") == "off";
        if (
          ($el.prop("checked") && !direction) ||
          (!$el.prop("checked") && direction)
        ) {
          self.sourceFilters.push({
            field: field,
            value: $el.val(),
            combine: $el.attr("data-combination") || "include",
          });

          if (field == "assignee_id") showClearFilterButton = true;
        }
      });

      this.setClearFiltersVisibility(showClearFilterButton);
      if (evt) {
        this.renderTaskList(); // don't re-render on initialization
      }
    },

    getAssignees: function (sortByName) {
      var self = this;
      var fields = JSON.stringify({
        User: {
          id: 0,
          name: 0,
          initials: 0,
          colour: 0,
        },
      });

      return new Promise(function (resolve, reject) {
        if (self.assignees) {
          resolve(self.assignees);
        } else {
          self.assignees = [];
          $.ajax({
            method: "get",
            dataType: "json",
            url: `/case/${window.dit.caseId}/team/json/`,
            data: { fields: fields },
          }).then(
            function (results) {
              _.each(results, function (result) {
                self.assignees.push({
                  key: result.user.id,
                  id: result.user.id,
                  name: result.user.name,
                  colour: result.user.colour,
                  initials: result.user.initials,
                });
              });

              if (sortByName) {
                self.assignees.sort(function (a, b) {
                  return a.name.localeCompare(b.name);
                });
              }

              resolve(self.assignees);
            },
            function () {
              resolve(self.assignees);
            }
          );
        }
      });
    },
    renderAssigneeFilter: function () {
      var self = this;
      this.getAssignees(true).then(function (assignees) {
        //assignees = assignees.concat(assignees);
        //assignees = assignees.concat(assignees);

        self.el
          .find(".assignee-filter")
          .html(
            self.templates["assigneeFilter"]({ self: self, users: assignees })
          );
      });
    },

    onModeChange: function (evt) {
      var listMode = $(evt.target).closest("div").find("input:checked").val();
      this.saveSettings({ listMode: listMode });
      this.updateMenu();
      this.renderTaskList();
    },

    updateMenu: function () {
      var self = this;
      var texts = {
        viewerMode: {
          bottom: "Switch to sliding viewer",
          slide: "Switch to lower viewer",
        },
        leftPanel: { right: "Task panel on left", left: "Task panel on right" },
      };
      this.el.find(".task-top-panel .function-menu button").each(function () {
        var key = $(this).val();
        var setting = self.settings[key];
        if (key == "leftPanel") {
          setting = GOVUK.getCookie("panel_side");
        }
        var text = (texts[key] || {})[setting];
        if (text) {
          $(this).text(text);
        }
      });
    },

    saveSettings: function (newSettings) {
      _.extend(this.settings, newSettings || {});
      window.localStorage["tasklist_settings"] = JSON.stringify(this.settings);
    },

    renderTaskList: function () {
      this.taskList.renderTaskList();
    },

    checkCache: function () {
      var self = this;
      if (this.cacheTimer) {
        window.clearTimeout(this.cacheTimer);
        delete this.cacheTimer;
      }
      $.ajax({
        method: "get",
        url: "/tasks/",
        data: { last: 1 },
      }).then(function (result) {
        self.lastUpdate = helpers.get(result, "result");
        if (
          self.lastUpdate &&
          window.localStorage["tasklist_lastupdate"] != self.lastUpdate
        ) {
          new Events().fire("tasks_updated");
        }
      });
      this.cacheTimer = setTimeout(this.checkCache, cachePollPeriod);
    },
  };
  return constructor;
});
