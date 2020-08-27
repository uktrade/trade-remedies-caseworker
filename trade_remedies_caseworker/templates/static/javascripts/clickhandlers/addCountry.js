/* Add country functionality

on change of a select, insert the selected thing into a block using a template.
Used where repeating blocks are present
click on a link and it -
* finds the closest item with a class of .row.
* removes it

*/
define([], function () {
  "use strict";

  function constructor(el) {
    var outer = el.closest(".form-group");
    var templateEl = outer.find(".template");
    var select = outer.find("select");
    var code = select.val();
    if (code) {
      var name = select.find("option:selected").text();
      var newEl = $(
        templateEl
          .html()
          .replace(/\(\(country_code\)\)/g, code)
          .replace(/\(\(name\)\)/g, name)
      );
      newEl.find("input").attr("name", "export_country_code");
      templateEl.parent().append(newEl);
      select.val("");
    }
  }

  return constructor;
});
