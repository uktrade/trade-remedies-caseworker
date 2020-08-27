// widget to upload a file
define(["modules/Events"], function (Events) {
  "use strict";

  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.eventDispatcher = new Events();
    _.bindAll(
      this,
      "positionButtons",
      "onClick",
      "onKeypress",
      "focusBack",
      "keydown"
    );
    this.multiline = this.el.attr("data-multiline");
    this.el.attr("tabindex", 0);
    _.bindAll(this, "save", "cancel", "val");
    el[0].val = this.val;
    el.on("click", this.onClick);
    el.on("keypress", this.onKeypress);
  };

  var activeInstance;

  var dialog_txt =
    '\
        <form action="/case/<%=obj.caseId%><% if(obj.model) {print("/"+obj.model+"/"+obj.id);}%>/" method="post">\
        <%=obj.csrfToken%>\
        <input type="hidden" name="redirect" value="<%=obj.redirect%>">\
        <h1 class="heading-small"></h1>\
        <div class="main-content">\
            <div class="form-group edit-item type-textArea">\
                <label class="form-label" for="content_text">Note text\
                <textarea id="content_text" name="<%=obj.name%>" class="form-control" rows="10" style="width:100%; height:100%;"><%=obj.content%></textarea>\
                <label>\
            </div>\
        </div>\
        <div class="form-group">\
            <button type="submit" class="button button-blue" name="btn-action" value="create">Save</button>\
            <button type="button" class="button button-grey pull-right dlg-close">Cancel</button>\
        </div>\
        </form>\
    ';

  var formTmp = _.template(
    '<form action="/case/<%=obj.caseId%><% if(obj.model) {print("/"+obj.model+"/"+obj.id);}%>/" method="post">\
        <%=obj.csrfToken%>\
        <!--<input type="hidden" name="redirect" value="<%=obj.redirect%>">-->\
        <input type="hidden" name="<%=obj.name%>" value="<%=obj.content%>">\
    </form>\
    ',
    { variable: "obj" }
  );

  var urlTmp = _.template(
    '/case/<%=obj.caseId%><% if(obj.model) {print("/"+obj.model+"/"+obj.id);}%>/',
    { variable: "obj" }
  );

  var dialog = _.template(dialog_txt, { variable: "obj" });

  var decodeElement = document.createElement("div");

  function decodeHTMLEntities(str) {
    // strip script/html tags
    str = str.replace(/<script[^>]*>([\S\s]*?)<\/script>/gim, "");
    str = str.replace(/<\/?\w(?:[^"'>]|"[^"]*"|'[^']*')*>/gim, "");
    decodeElement.innerHTML = str;
    str = decodeElement.textContent;
    decodeElement.textContent = "";
    return str;
  }

  function scrollBarWidth() {
    return 10;
  }

  function positionButtons() {
    // We can't attach the buttons in the right place by css so recalc with js.
    this.saveCancel &&
      this.saveCancel.css({
        "margin-left": this.el.width() - this.saveCancel.width() + "px",
        "margin-top":
          5 + this.el.height() + parseInt(this.el.css("margin-top")) + "px",
      });
  }

  function startEdit() {
    var self = this;
    if (activeInstance == this) {
      return;
    }
    activeInstance && activeInstance.cancel();
    activeInstance = this;
    // check for other editors.
    this.container = this.el.closest(".well, .section");
    this.sources = this.container.find(".editable");

    // create save/cancel buttons
    //this.saveCancel = $('<div class="edit-buttons"><button class="save"><img class="icon icon-tick"></button><button class="cancel"><img class="icon icon-cross"></button></div>');
    this.saveCancel = $(
      '<div class="edit-buttons"><button type="button" class="save">&#x2713;</button><button type="button" class="cancel">&#x2715;</button></div>'
    );
    this.el.before(this.saveCancel);
    this.originalHtml = this.el.html();
    // attach handlers
    this.saveCancel.find(".save").on("click", this.save);
    this.saveCancel.find(".cancel").on("click", this.cancel);
    this.saveCancel.css({
      "margin-left": this.el.width() - this.saveCancel.width() + "px",
      "margin-top":
        5 + this.el.height() + parseInt(this.el.css("margin-top")) + "px",
    });

    this.el.on("focusout", this.focusBack);
    var source = this.el;
    //editElement = $('<textarea class="inplaceEdit"/>')
    source.attr("contenteditable", true);
    //source.focus();
    source.addClass("editing");
    this.el.on("keydown", this.keydown);
  }

  function getDialog(callback, title, data) {
    require(["modules/Lightbox"], function (Lightbox) {
      callback(
        new Lightbox({
          title: title,
          content: dialog(
            _.extend({ redirect: window.location.href }, window.dit, data || {})
          ),
          buttons: { ok: 1, cancel: 1 },
        })
      );
    });
  }

  constructor.prototype = {
    focusBack: function (evt) {
      console.log("focus back");
      var self = this;
      this.el.focus();
    },

    onClick: function (evt) {
      startEdit.call(this);
    },

    onKeypress: function (evt) {
      if (this != activeInstance) {
        if (evt.keyCode == 13) {
          evt.preventDefault();
          startEdit.call(this);
        }
      }
    },

    keydown: function (evt) {
      switch (evt.keyCode) {
        case 13:
          if (!this.multiline) {
            evt.preventDefault();
            this.save();
          }
          break;
        case 9:
          evt.preventDefault();
          this.saveCancel.find("button").first().focus();
          break;
        case 27:
          evt.preventDefault();
          this.cancel();
          break;
      }
      this.posTimer && clearTimeout(this.posTimer);
      this.posTimer = setTimeout(this.positionButtons);
    },

    positionButtons: function () {
      // We can't attach the buttons in the right place by css so recalc with js.
      this.saveCancel &&
        this.saveCancel.css({
          "margin-left": this.el.width() - this.saveCancel.width() + "px",
          "margin-top":
            5 + this.el.height() + parseInt(this.el.css("margin-top")) + "px",
        });
    },

    val: function () {
      var html = this.el.html().replace(/\n/g, "").trim();
      var newValue = decodeHTMLEntities(
        html.replace(/\<(?:(?:br)|(?:div))\>/g, "\n").replace(/\<\/div\>/g, "")
      );
      if (newValue == "\n") {
        newValue = "";
        this.el.html("");
      }
      return newValue;
    },

    stopEdit: function (save) {
      if (this == activeInstance) {
        activeInstance = null;
        var self = this;
        this.el.attr("contenteditable", false);
        this.saveCancel.remove();
        this.saveCancel = null;
        this.el.removeClass("editing");
        this.el.off("keydown", this.keydown);
        this.el.off("focusout", this.focusBack);
        if (save) {
          var html = this.el.html().replace(/\n/g, "").trim();
          var newValue = decodeHTMLEntities(
            html
              .replace(/\<(?:(?:br)|(?:div))\>/g, "\n")
              .replace(/\<\/div\>/g, "")
          );
          if (newValue == "\n") {
            newValue = "";
            this.el.html("");
          }
          this.el[0].value = newValue;
          this.el.trigger("change");
          var id = this.el.attr("data-id");
          if (id) {
            var data = {
              csrfmiddlewaretoken: window.dit.csrfToken,
              case_id: window.dit.caseId,
              id: this.el.attr("data-id"),
              model: this.el.attr("data-model"),
              btn_value: "save",
            };

            data[this.el.attr("data-name")] = newValue;

            $.ajax({
              url:
                data.model == "task"
                  ? "/tasks/"
                  : urlTmp(_.extend(window.dit, data || {})),
              type: "POST",
              data: data,
            }).then(function (result) {
              // TODO: Convert response to json and check for errors here
              //(this.element[0].onupdate || _.noop)(result);
              self.eventDispatcher.fire("In-place-edit-save", {
                result: result,
              });
            });

            /*
                        var form = $(formTmp(_.extend({redirect:window.location.href},window.dit, data || {})));
                        $(document.body).append(form);
                        form.submit();
                        form.remove();
                        */
          }
        } else {
          this.el.html(this.originalHtml);
        }
      }
    },

    save: function () {
      this.stopEdit(true);
    },

    cancel: function () {
      this.stopEdit();
    },
  };

  return constructor;
});
