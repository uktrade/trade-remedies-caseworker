// widget to upload a file
define(function () {
  "use strict";
  function constructor(el) {
    require(["modules/WorkflowEditor"], function (Editor) {
      var workflow = JSON.parse($("#workflow-json").val());
      var state = JSON.parse($("#state-json").val());
      new Editor(el, workflow, state);
    });
  }

  return constructor;
});
