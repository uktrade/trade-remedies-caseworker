// Typeahead - using the jqueryUI autocomplete widget
define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.root = this.el.siblings(".expand-section");
    this.root.css({ height: "auto" });
    this.rootHeight = this.root.height() + "px";
    this.root.css({ height: "0px" });
    el.on("click", _.bind(onClick, this));
  };

  var dlg;

  var dialog = _.template(
    '\
        <form action="/case/<%=caseId%>/section/" method="post">\
        <%=csrfToken_input %>\
        <input type="hidden" name="parent_id" value="<%=parent_id%>">\
        <h1 class="heading-small"><%=title%></h1>\
        <div class="main-content">\
            <div class="form-group edit-item type-text">\
                <label class="form-label" for="field-name">Name</label>\
                <input type="text" name="name" class="form-control"/>\
            </div>\
            <div class="form-group edit-item type-textArea">\
                <label class="form-label" for="content_text">Description\
                <textarea id="content_text" name="content" class="form-control" rows="10" style="width:100%; height:100%;"></textarea>\
                <label>\
            </div>\
        </div>\
        <div class="form-group">\
            <button type="submit" class="button button-blue" name="btn-action" value="create">Save</button>\
            <button type="button" class="button button-grey pull-right dlg-close">Cancel</button>\
        </div>\
        </form>\
    '
  );

  function getDialog(title, parent, callback) {
    require(["modules/Lightbox"], function (Lightbox) {
      new Lightbox({
        title: "Create section",
        content: dialog(
          _.extend({ title: title, parent_id: parent }, window.dit)
        ),
        buttons: { ok: 1, cancel: 1 },
      });
    });
    return;
    /*
        require(['jqui/widgets/dialog'],function(dialog) {
            dlg = dlg || $( "#create-page-form" ).dialog({
                autoOpen: false,
                height: 400,
                width: 350,
                modal: true,
                buttons: {
                    "Do it": function(){alert('bing');},
                    Cancel: function() {
                      dlg.dialog( "close" );
                    }
                },
                close: function() {
                   // form[ 0 ].reset();
                   //allFields.removeClass( "ui-state-error" );
                }
            });
            callback(dlg)
        })
*/
  }

  function createItem(link) {
    var title = link.attr("data-title");
    var parentId = link.attr("data-parent");
    getDialog(title, parentId, function (dialog) {
      dialog.dialog("open");
    });
  }

  function onClick(evt) {
    var link = $(evt.target).closest("a.add-link");
    if (link.length) return createItem(link);
    /*        var li = $(evt.target).closest('li');
        var ol = li.children('ol');
        var expand = !li.hasClass('expanded');
        li.toggleClass('expanded');
        if(expand) {
            ol.css({display: 'block', height:'auto'});
            var height = ol.height();
            ol.css({height:'0'});
            window.setTimeout(function() {
                ol.css({height:height + 'px'});
            },0);
            window.setTimeout(function(){
                ol.css({height:'auto'});
            },300)
        } else {
            var height = ol.height();
            ol.css({height:height+'px'});
            window.setTimeout(function() {
                ol.css({height:'0px'});
            },0);          
        } */
  }

  return constructor;
});
