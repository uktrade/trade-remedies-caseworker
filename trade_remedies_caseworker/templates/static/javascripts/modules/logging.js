if (window.dit.environment != "production") {
  define(["vendor/debug"], function (debug) {
    function DebugLogger(name) {
      const namespace = `case:${name}`;
      const dbg = debug(namespace);

      return {
        log: dbg,
      };
    }

    return {
      getLogger: DebugLogger,
    };
  });
} else {
  define([], function () {
    function NullLogger(name) {
      function dbg() {}

      return {
        log: dbg,
      };
    }

    return {
      getLogger: NullLogger,
    };
  });
}
