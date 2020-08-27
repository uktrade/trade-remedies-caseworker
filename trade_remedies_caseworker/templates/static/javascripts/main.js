// attach widget

define("jquery", [], function () {
  return jQuery;
});

var widgets = [
  {
    selector: ".modal-form",
    module: "ModalForm",
  },
  {
    selector: "form.validate",
    module: "Validate",
  },
  {
    selector: "main",
    module: "Debounce",
  },
  {
    selector: "main",
    module: "PopUpDetails",
  },
];

$(function () {
  $.fn.extend({
    setClass: function (className, set) {
      var self = this;
      this.each(function (idx, el) {
        var $el = self.constructor(el);
        if ($el.hasClass(className) != !!set) {
          $el.toggleClass(className);
        }
      });
      return self;
    },
    attachWidgets: function () {
      var self = this;
      this.each(function (idx, container) {
        var $container = self.constructor(container);
        // Explicit attached modules
        $container.find("[data-attach]").each(function (idx) {
          var el = this;
          var moduleName = $(el).attr("data-attach");
          if (!el[moduleName]) {
            el[moduleName] = 1;
            require(["widgets/" + moduleName], function (module) {
              var mod = new module($(el));
              el[moduleName] = mod || 1;
            });
          }
        });
        // general modules
        _.each(widgets, function (widget) {
          $container.find(widget.selector).each(function (idx) {
            var el = this;
            if (!el[widget.module]) {
              el[widget.module] = 1;
              require(["widgets/" + widget.module], function (module) {
                el[widget.module] = new module($(el)) || true;
              });
            }
          });
        });
      });

      return self;
    },
  });

  requirejs.config({
    baseUrl: dit.jsBase,
    paths: {
      widgets: "widgets",
      vendor: "vendor",
      jqui: "vendor/ui",
      modules: "modules",
    },
  });

  $(document.body).on("mousedown", function (evt) {
    // stop a click on a link from focussing it
    if ($(evt.target).closest("a").length) {
      evt.preventDefault();
    }
  });

  $(document.body).attachWidgets();
  var semaphore;

  $(document).ajaxComplete(function (event, xhr, settings) {
    if (xhr.responseText.substr(1, 10).indexOf("#32;") >= 0) {
      // It's the login page!.  This is a special indicator
      event.preventDefault();
      if (!semaphore) {
        semaphore = true;
        var start = xhr.responseText.indexOf("<main");
        var end = xhr.responseText.indexOf("</main>") + 7;
        content = xhr.responseText.substring(start, end);
        require(["modules/Lightbox"], function (Lightbox) {
          var lb = new Lightbox({ content: content });
          lb.getContainer()
            .find("form")
            .on("submit", function (evt) {
              evt.preventDefault();
              var form = $(this);
              $.ajax({
                url: form.attr("action"),
                method: "post",
                data: form.serialize(),
              }).then(function (result) {
                lb.close(); // We close whatever as if the login is unsuccesful, another instance will be fired up.
                semaphore = false;
              });
            });
        });
      }
    }
  });
  // Load the form builder
  /*	require(['modules/helpers'],function(helpers) {
		if(helpers.urlParameters().config) {
			localStorage.config = helpers.urlParameters().config;
		}

		if(localStorage.config == 'on') {
			require(['modules/formBuilder'], function(formBuilder) {
			})
		}

	}) */
});
