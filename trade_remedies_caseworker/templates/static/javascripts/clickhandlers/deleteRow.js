/* Remove a row from an add/remove widget

Used where repeating blocks are present
click on a link and it -
* finds the closest item with a class of .row.
* removes it

*/
define([], function () {
  "use strict";

  function constructor(el) {
    var row = el.closest(".row, li");
    var count = row.parent().find(".row, li").length;
    if (count > 1) {
      el.closest(".row, li").remove();
    }
  }
  return constructor;
});
