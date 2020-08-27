// Switch between review and edits on a section in the bundle builder
define([], function () {
  "use strict";

  function constructor(el) {
    // Toggle the edit section
    var section = el.closest(".section");
    el.closest(".section").toggleClass("populated");
    // hide the current edit section
    $(".edit-section").each(function () {
      var elSection = $(this).closest(".section");
      if (!elSection.is(".populated") && elSection[0] != section[0]) {
        elSection.hide();
      }
    });
    // Hide other edit buttons
    $("button.edit[data-handler=switchSection]").hide();
    // switch to the edit set of buttons
    $(".button-group")
      .addClass("editing")
      .removeClass("publishing")
      .removeClass("issuing");
  }

  return constructor;
});
