// Validate - client-side form validation
define(function () {
  "use strict";
  var constructor = function (el) {
    this.$form = el;
    el[0].validate = _.bind(onSubmit, this);
    this.$form.on("submit", el.validate);
  };

  function onSubmit(evt) {
    // check for required fields on the form
    if (!this.$form.attr("no-validate")) {
      var populated = {};
      _.each(this.$form.serializeArray(true), function (item) {
        populated[item.name] = item.value;
      });
      var failed;
      this.$form.find(".error").removeClass("error");
      this.$form.find(".error-message").remove();
      this.$form.find(".form-group[data-validate]:visible").each(function () {
        var group = $(this);
        var validation = group.attr("data-validate");
        _.each(validation.split("||"), function (valStr) {
          var parts = valStr.split("->");
          var name = group.find("[name]").prop("name");
          var value = populated[name] || "";
          var reg = new RegExp(parts[0]);
          if (!reg.test(value)) {
            group
              .addClass("error")
              .children("label")
              .first()
              .after(
                '<span class="error-message">' +
                  (parts[1] || "Failed validation") +
                  "</div>"
              );
            failed = true;
          }
        });
      });
    }
    return failed;
  }

  return constructor;
});
