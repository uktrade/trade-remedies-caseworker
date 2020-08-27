define([], function () {
  var bounceContainer;

  var notifyTemplate = _.template(
    `<div class="bouncy"><i class="icon <%=icon%>"></i><div><h1><%=title%></h1><%=message%></div>`
  );

  return {
    confirm: function (message, title) {
      return new Promise(function (resolve, reject) {
        require(["modules/Lightbox"], function (Lightbox) {
          var lb = new Lightbox({
            title: title || "Confirm",
            message: message,
            buttons: { ok: 1, cancel: 1 },
          });
          var container = lb.getContainer();
          setTimeout(function () {
            container.find("button[value='ok']").focus();
          }, 0);
          lb.getContainer()
            .find("button")
            .on("click", function (evt) {
              if ($(evt.target).val() == "ok") {
                resolve();
              } else {
                reject();
              }
            });
        });
      });
    },

    alert: function (message, title) {
      return new Promise(function (resolve, reject) {
        require(["modules/Lightbox"], function (Lightbox) {
          var lb = new Lightbox({
            title: title || "Information",
            message: message,
            buttons: { ok: 1 },
          });
          lb.getContainer()
            .find("button")
            .on("click", function (evt) {
              resolve();
            });
        });
      });
    },

    error: function (message, title) {
      return new Promise(function (resolve, reject) {
        require(["modules/Lightbox"], function (Lightbox) {
          var lb = new Lightbox({
            title: title || "Error",
            message: message,
            buttons: { ok: 1 },
          });
          lb.getContainer()
            .find("button")
            .on("click", function (evt) {
              resolve();
            });
        });
      });
    },

    notify: function (message, title) {
      title = title || "Alert";
      var icon = "icon-green-tick";
      if (!bounceContainer) {
        bounceContainer = $('<div class="alert-container"></div>');
        $(document.body).append(bounceContainer);
      }
      var div = $(
        notifyTemplate({ title: title, message: message, icon: icon })
      );
      bounceContainer.append(div);
      setTimeout(function () {
        div.css({ transition: "opacity 3s", opacity: 0 });
        setTimeout(function () {
          div.remove();
        }, 3000);
      }, 3000);
    },
  };
});
