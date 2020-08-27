/* Template clone

Used where repeating blocks are required
click on a link and it -
* finds the closest form-group, then the first container with a class 'template' within it.
* clones said template, clears any input values and appends to the template container

*/
define(["modules/helpers", "modules/popUps"], function (helpers, popups) {
  "use strict";

  function constructor(el) {
    var template = el.closest(".form-group").find(".template").first();
    var container = template.parent();
    var el = template.clone();
    el.find("input").val("");
    container.append(el);
  }

  return constructor;
});
