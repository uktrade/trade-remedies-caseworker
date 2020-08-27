// Dynamic substitution of notify templates
define([], function () {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    this.form = this.el.is("form") ? this.el : this.el.find("form").first();
    if (!this.form.length) {
      this.form = el.closest("form");
    }
    this.previewEl = this.el.find(".notify-preview");
    this.form.on("change", _.bind(onChange, this));
    switchTags.call(this);
    // set up initial values
    this.form.find("input, select").each(function () {
      $(this).trigger("change");
    });
  };

  function switchTags() {
    var self = this;
    var template = this.previewEl.html();
    var reg = /\(\(([^\)]+)\)\)/g;
    var subst = template.replace(
      reg,
      '<span class="notify-tag unpopulated" data-name="$1" title="$1">&lt;empty&gt;</span>'
    );
    self.previewEl.html(subst);
    self.tagList = {};
    self.previewEl.find(".notify-tag").each(function () {
      var tagName = $(this).attr("data-name");
      tagName && (self.tagList[tagName] = $(this));
    });
  }

  function onChange(evt) {
    var target = $(evt.target);
    var name = target.attr("data-substitute") || target.attr("name");
    var value = target.attr("data-text-value") || target.val();
    var tag = target.prop("tagName");
    if (tag == "SELECT") {
      // If the value is blank - it's the select line, so leave empty
      var option = target.find("option:selected");
      value = value && (option.attr("data-text-value") || option.text());
    }
    var subst = this.tagList[name];
    if (subst) {
      subst.text(value || "((" + name + "))").setClass("unpopulated", !value);
    }
  }

  return constructor;
});
