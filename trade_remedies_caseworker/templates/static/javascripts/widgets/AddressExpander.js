define([], function () {
  "use strict";
  var transitionDuration = 300;

  var constructor = function (el) {
    this.el = el;
    if (!el.prop("clientHeight")) {
      this.el
        .closest(".expand-section, .tab-page")
        .on("show", _.bind(onShow, this));
    } else {
      onShow.call(this);
    }
  };

  function onShow(evt) {
    if (!this.initialized) {
      this.initialized = true;
      this.contactBlock =
        this.contactBlock || this.el.closest(".contact-block");
      var startHeight = this.contactBlock.height();
      this.contactBlock.css({ height: "auto" });
      var freeHeight = this.contactBlock.height();

      var diff = freeHeight - startHeight;
      if (diff > 0) {
        // It's collapsed a bit
        this.address = this.el.find(".address");
        this.innerHeight = this.address.prop("offsetHeight");
        this.outerHeight = this.innerHeight - diff - 30;
        this.expanded = false;
        this.expander = $(
          '<div class="fold-controls"><div class="shader"></div><a class="pull-right" href="javascript:void(0)"><span>Show all</span> <i class="icon icon-down rotate correct"></i></a></div>'
        );
        this.address.after(this.expander);
        this.expander.find("a").on("mousedown", _.bind(mouseDown, this)); // so the link doesn't focus
        this.expander.find("a").on("click", _.bind(onClick, this)); // to pick up keyboard clicks
        this.address.css({ height: this.outerHeight + "px" });
        //  as we have reduced the height of the address, we can loose the contact block
        this.contactBlock.css({ height: "" });
      } else {
        this.contactBlock.css({ height: "" });
      }
    }
  }

  function mouseDown(evt) {
    evt.preventDefault();
  }

  function onClick(evt) {
    var self = this;
    evt.preventDefault(); // kill the focus
    this.expanded = !this.expanded;
    this.address.css({
      height: (this.expanded ? this.innerHeight : this.outerHeight) + "px",
    });
    this.contactBlock.css({ height: "auto" });
    if (this.expanded) {
      this.contactBlock.addClass("expanded");
    } else {
      setTimeout(function () {
        self.contactBlock.removeClass("expanded");
      }, transitionDuration);
    }
    this.expander.find("span").text(this.expanded ? "Show less" : "Show all");
    this.expander.find("i.rotate").setClass("rotated", this.expanded);
    return false;
  }

  return constructor;
});
