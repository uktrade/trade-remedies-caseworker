define([], function () {
  var monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  var dayNames = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
  var zeros = "0000000000000";
  var templateStore = {};
  var millisPerDay = 1000 * 60 * 60 * 24;
  Date.prototype.getDayName = function () {
    return dayNames[this.getDay()];
  };
  Date.prototype.getMonthName = function () {
    return monthNames[this.getMonth()];
  };
  Date.prototype.toISOString = function () {
    //uppercase
    return `${("" + this.getFullYear()).pad(4)}-${(
      "" +
      (this.getMonth() + 1)
    ).pad(2)}-${("" + this.getDate()).pad(2)}T00:00:00`;
  };
  Date.parseIso = function (str) {
    // parse a 'yyy-mm-ddThh:mm:ss' date string
    if (!_.isString(str)) {
      return new Date(str);
    }
    var bits = (str || "").match(
      /(\d{4})-(\d{1,2})-(\d{1,2})(?:T(\d{1,2})(?:\:(\d{1,2}))?(?:\:(\d{1,2}))?)?/
    );
    if (bits)
      return new Date(
        bits[1],
        bits[2] - 1,
        bits[3],
        bits[4] || 0,
        bits[5] || 0,
        bits[6] || 0
      );
    bits = (str || "").match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    return bits && new Date(bits[3], bits[2] - 1, bits[1], 0, 0, 0);
  };

  Date.prototype.formatDue = function () {
    var diff = 0 - (new Date() - this);
    var days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    if (days > 25) {
      return Math.floor(days / 7) + " wks";
    }
    if (days < 0) {
      return `<span class="overdue">${0 - days} day${
        0 - days > 1 ? "s" : ""
      } ago</span>`;
    }
    if (days == 0) {
      return `<span class="overdue">Today</span>`;
    }
    return days + ` day${days > 1 ? "s" : ""}`;
  };

  var timeDivisions = [
    { div: 1000, message: "moments ago", threshold: 60 },
    { div: 60, name: "minute" },
    { div: 60, name: "hour" },
    { div: 24, name: "day" },
    { div: 7, name: "week" },
    { div: 52, name: "year" },
    { div: 500 },
  ];

  Date.prototype.formatAgo = function () {
    var diff = new Date() - this;
    for (var i = 0; i < timeDivisions.length; i++) {
      var div = timeDivisions[i];
      diff = Math.floor(diff / div.div);
      if (diff < timeDivisions[i + 1].div) {
        return div.name
          ? `${diff} <span>${div.name}${diff > 1 ? "s" : ""} ago</span>`
          : div.message;
      }
    }
  };

  Date.prototype.format = function (template) {
    var tmp = templateStore[template];
    if (!tmp) {
      // we don't have this format already compiled

      var rTemplate = template
        .replace("yyyy", "<%=dt.getFullYear()%>")
        .replace("month", '<%=(""+(dt.getMonthName(1))) %>')
        .replace("mon", '<%=(""+(dt.getMonthName())) %>')
        .replace("mm", '<%=(""+(1+dt.getMonth())).pad(2)%>')
        .replace("dd", '<%=(""+dt.getDate()).pad(2)%>');
      rTemplate = rTemplate
        .replace("HH", '<%=(""+dt.getHours()).pad(2)%>')
        .replace("MM", '<%=(""+dt.getMinutes()).pad(2)%>')
        .replace("SS", '<%=(""+dt.getSeconds()).pad(2)%>')
        .replace("MS", '<%=(""+dt.getMilliseconds()).pad(3)%>')
        .replace("day", "<%=dt.getDayName()%>");
      rTemplate = rTemplate
        .replace("$ago", '<%=(""+dt.formatAgo())%>')
        .replace("$due", '<%=(""+dt.formatDue())%>');

      //var rTemplate = template.replace('yyyy','<%=dt.getUTCFullYear()%>').replace('month','<%=(""+(dt.getUTCMonthName(1))) %>').replace('mon','<%=(""+(dt.getUTCMonthName())) %>').replace('mm','<%=(""+(1+dt.getUTCMonth())).pad(2)%>').replace('dd','<%=(""+dt.getUTCDate()).pad(2)%>');
      //rTemplate = rTemplate.replace('HH','<%=(""+dt.getUTCHours()).pad(2)%>').replace('MM','<%=(""+dt.getUTCMinutes()).pad(2)%>').replace('SS','<%=(""+dt.getUTCSeconds()).pad(2)%>').replace('MS','<%=(""+dt.getUTCMilliseconds()).pad(3)%>');
      tmp = templateStore[template] = _.template(rTemplate, { variable: "dt" });
    }
    return tmp(this);
  };
  Date.prototype.addDays = function (days) {
    return new Date(this.getTime() + days * millisPerDay);
  };
  Date.prototype.round = function () {
    return new Date(Math.round(this.getTime() / millisPerDay) * millisPerDay);
  };

  String.prototype.pad = function (length) {
    return zeros.substring(0, length - this.length) + this;
  };

  function deepExtend(obj1, obj2) {
    _.each(obj2, function (value, key) {
      if (_.isObject(obj1[key]) && _.isObject(value)) {
        deepExtend(obj1[key], value);
      } else {
        if (value == "(delete)") {
          delete obj1[key];
        } else {
          obj1[key] = value;
        }
      }
    });
    return obj1;
  }

  function serializeArray(els) {
    // Replace the jquery serializer with one that includes disabled controls
    var out = [];
    els.each(function () {
      var $el = $(this);
      var name = $el.attr("name");
      if (name) {
        var val = $el.val();
        var tagName = $el.prop("tagName");
        if (tagName == "DIV") {
          val = $el[0].val();
        }
        if ($el.attr("type") in { radio: 1, checkbox: 1 }) {
          if ($el.prop("checked")) {
            out.push({ name: name, value: val });
          }
        } else {
          out.push({ name: name, value: val });
        }
      }
    });
    return out;
  }

  function parsePythonBool(value) {
    //Expecting values of True or False anything else will raise an error
    if (typeof value === "undefined") throw "Unable to parse";
    if (value == "True") return true;
    if (value == "False") return false;

    throw `Expected True or False but received ${value}`;
  }

  var library = {
    parsePythonBool: parsePythonBool,
    urlParameters: function (map) {
      // Return the url (get) parameters as a map
      // .. or pass in a map to set all url parameters and load page.
      var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split("&"),
        out = {};
      if (map) {
        var arr = [];
        _.each(map, function (val, key) {
          arr.push(key + "=" + val);
        });
        window.location.assign("?" + arr.join("&"));
        return;
      } else {
        for (var i = 0; i < sURLVariables.length; i++) {
          var dec = decodeURIComponent(sURLVariables[i]);
          var split = dec.split("=");
          out[split[0]] = split[1] || "1";
        }
        return out;
      }
    },
    hashParameters: function (vals, assign) {
      var hashParams = {};
      _.each(location.hash.replace(/^\#/, "").split("&"), function (part) {
        var pair = part.split("=");
        hashParams[pair[0]] = pair[1];
      });
      if (vals) {
        // something to update
        _.extend(hashParams, vals);
        var out = [];
        _.each(hashParams, function (value, key) {
          if (value || value === 0) {
            out.push(key + "=" + value);
          }
        });
        var url =
          location.protocol +
          "//" +
          location.hostname +
          ":" +
          location.port +
          location.pathname +
          location.search +
          "#" +
          out.join("&");
        location[assign ? "assign" : "replace"](url);
      }
      return hashParams;
    },

    unMap: function (arr) {
      // return an object from an array of name/value pairs
      var out = {};
      _.each(arr, function (obj) {
        if (_.isString(obj)) {
          out[obj] = true;
        } else {
          out[obj.name] = obj.value;
        }
      });
      return out;
    },
    map: function (obj) {
      // Map an object to an array of name/value objects
      var out = [];
      _.each(obj, function (value, key) {
        out.push({ name: key, value: value });
      });
      return out;
    },
    index: function (arr, key) {
      // provide an index(map) of elements in array or object
      var out = {};
      var needsGet = key.indexOf(".") > 0;
      _.each(arr, function (item) {
        val = needsGet ? library.get(item, key, "") : item[key] || "";
        (out[val] = out[val] || []).push(item);
      });
      return out;
    },
    get: function (obj, path, def) {
      var spl = path.split(".");
      obj = obj || {};
      for (var idx = 0; idx < spl.length; idx++) {
        if (!_.isObject(obj)) return def;
        obj = obj[spl[idx]];
      }
      return obj;
    },
    pad: function (str, digits, char) {
      // zero pad to the  number of digits given
      str = "" + str;
      var len = Math.max(0, digits - str.length);
      return new String(char || "0").repeat(len) + str;
    },
    deepExtend: deepExtend,
    serializeArray: serializeArray,
  };
  window.helpers = library;
  return library;
});
