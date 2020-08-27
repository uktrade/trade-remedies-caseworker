/* Slider handler

Toggle a slider state

*/

define(["modules/logging"], function (logging) {
  "use strict";
  const logger = logging.getLogger("slider");

  function constructor(el) {
    logger.log("ctor");
    el.find("input").each(function () {
      el[$(this).prop("checked") ? "addClass" : "removeClass"]($(this).val());
    });

    el.on("keydown", function (evt) {
      if (evt.keyCode == 13) {
        $(evt.target).closest("label").trigger("click");
      }

      el.find("input").each(function () {
        el[$(this).prop("checked") ? "addClass" : "removeClass"]($(this).val());
      });
    });

    el.on("click", function (evt) {
      logger.log("slider click");
      el.find("input").each(function () {
        logger.log("update state");
        el[$(this).prop("checked") ? "addClass" : "removeClass"]($(this).val());
      });
    });
  }

  return constructor;
});
