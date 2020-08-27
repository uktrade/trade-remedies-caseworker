define([], function () {
  "use strict";

  function constructor(el) {
    const selector = ".user-list-container";
    const outer = el.closest(selector);

    if (!outer.length) {
      throw "Expected to find " + selector;
    }

    $(outer).toggleClass("show-all-users");
  }

  return constructor;
});
