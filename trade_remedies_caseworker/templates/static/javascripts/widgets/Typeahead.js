// Typeahead - using the jqueryUI autocomplete widget
define(["modules/helpers"], function (helpers) {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el.find("input").first();
    el.attr("id", "autocomplete-menu");
    if ((this.settings = settings[this.el.attr("data-mode")])) {
      require(["jqui/widgets/autocomplete"], function (autocomplete) {
        self.el.autocomplete({
          source: _.bind(search, self),
          select: _.bind(select, self),
          appendTo: "#autocomplete-menu",
          minLength: self.settings["minLength"] || 1,
        });
      });
      var onChange;
      if ((onChange = self.settings["onChange"])) {
        self.el.on("change", _.bind(onChange, self));
      }
    } else {
      console.error(
        'Unknown typeahead settings - "' + self.el.attr("data-mode") + '"'
      );
    }
  };

  var addressFields = [
    { key: "premises", postStr: ",\n", postStrNumeric: "," },
    { key: "address_line_1", postStr: ",\n" },
    { key: "address_line_2", postStr: ",\n" },
    { key: "address_line_3", postStr: ",\n" },
    { key: "locality", postStr: ",\n" },
    { key: "region", postStr: ",\n" },
    { key: "postal_code", postStr: "" },
  ];

  var settings = {
    productCat: {
      url: "https://selling-online-overseas.export.great.gov.uk/products/api/",
      getParameters: function (request) {
        return { q: request.term };
      },
      processResult: function (data) {
        var result = [];
        _.each(data.categories, function (sub) {
          _.each(sub, function (cat) {
            result.push({ label: cat, value: cat });
          });
        });
        return result;
      },
    },
    company: {
      url: "/companieshouse/search/",
      getParameters: function (request) {
        return request;
      },
      processResult: function (data) {
        var result = [];
        var store = (this.data = {});
        _.each(data, function (company) {
          store[company.title] = company;
          result.push({
            label: company.title + "\n" + company.address_snippet,
            value: company.title,
          });
        });
        return result;
      },
      onSelect: function (event, ui) {
        var item = ui.item;
        var res = this.data[item.value] || {};
        res.full_address = "";
        _.each(addressFields, function (def) {
          if (def.key in res.address) {
            var val = (res.address[def.key] || "").trim();
            var postStr =
              def.postStrNumeric && /^[0-9A-Z]{1,4}$/i.test(val)
                ? def.postStrNumeric
                : def.postStr;
            res.full_address += val + postStr;
          }
        });
        _.each(res.address, function (value, key) {
          $("#" + key).val(value);
        });
        _.each(res, function (value, key) {
          $("#" + key).val(value);
        });
      },
    },
    postcode: {
      //url:'https://api.getAddress.io/find',
      getUrl: function (request) {
        if (request.term.length >= 6)
          return "https://postcodes.io/postcodes/" + request.term;
      },
      getParameters: function (request) {
        return {
          postcode: request.term,
        };
      },
      processResult: function (data) {
        return [];
      },
    },
    contactEmail: {
      url: "/users/contact_lookup/",
      getParameters: function (request) {
        return {
          email: request.term,
        };
      },
      processResult: function (data) {
        var result = [];
        _.each(data.result, function (contact) {
          result.push({
            label: `${contact.email} - ${contact.name}`,
            value: contact.email,
            name: contact.name,
            id: contact.id,
            address: contact.address,
            country: contact.country,
            phone: contact.phone,
            organisation: contact.organisation,
          });
        });
        return result;
      },
      minLength: 2,
      onChange: function (evt) {
        var self = this;
        if (this.email != this.el.val()) {
          self.el.closest("form").attr("no-validate", false);
          _.each(this.items, function (input, key) {
            input.val("").removeAttr("readonly");
          });
          _.defer(function () {
            self.items["contact_name"].focus();
          });
        }
      },
      onSelect: function (event, ui) {
        var self = this;
        self.items = self.items || {};
        $.ajax({
          method: "get",
          dataType: "json",
          url: self.settings.url,
          data: { contact_id: ui.item.id },
        }).then(function (result) {
          self.el
            .closest("form")
            .attr("no-validate", true)
            .find("[data-key]")
            .each(function () {
              var $el = $(this);
              var value = helpers.get(result.result, $el.attr("data-key"));
              $el
                .val(value)
                .not("[type=hidden]")
                .attr("readonly", this != self.el[0]);
              if (this == self.el[0]) {
                self.email = value;
              } else {
                self.items[$el.attr("name")] = $el;
              }
            });
        });
      },
    },
  };

  function search(request, response) {
    var self = this;
    var settings = this.settings;
    if (this.xhr) {
      this.xhr.abort();
    }
    var url = settings.url || settings.getUrl(request);
    if (url) {
      this.xhr = $.ajax({
        url: url,
        data: settings.getParameters.call(self, request),
        dataType: "json",
        success: function (data) {
          response(settings.processResult.call(self, data));
        },
        error: function () {
          response([]);
        },
      });
    }
  }

  function select(event, ui) {
    (this.settings.onSelect || _.noop).call(this, event, ui);
  }

  constructor.prototype = {
    enable: function (enableState) {
      this.el.autocomplete({ true: "enable", false: "disable" }[enableState]);
    },
  };

  return constructor;
});
