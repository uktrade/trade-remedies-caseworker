define(["modules/helpers"], function (helpers) {
  "use strict";

  return {
    getTaskList: function () {
      var self = this;
      return new Promise(function (resolve, reject) {
        var tasks;
        // build a query
        var query = [];
        _.each(self.controller.sourceFilters, function (filter) {
          switch (filter.field) {
            case "all_tasks":
              break;
            default:
              query.push({
                field: filter.field,
                value: filter.value,
                combine: filter.combine,
              });
          }
        });

        if (window.dit.caseId) {
          query.push({ field: "case_id", value: window.dit.caseId });
        } else {
          query.push({ field: "status", value: "nwd", combine: "not" }); // if we are looking outside case, need to exclude NWDs
        }

        if (window.localStorage["tasklist_lastupdate"] == self.lastUpdate) {
          // Nothing has changed so get tasks from cache
          try {
            var cacheStr = window.localStorage["tasklist_data"];
            var cache = JSON.parse(cacheStr);
            if (cache.query == JSON.stringify(query)) {
              tasks = cache.tasks;
            }
          } catch (e) {}
          if (tasks && _.isArray(tasks)) {
            resolve(tasks);
            return;
          }
        }
        // We need to get the tasks anew
        // build filters
        let data = {
          query: JSON.stringify(query),
          fields: JSON.stringify({
            Task: {
              id: 0,
              case_id: 0,
              case: {
                reference: 0,
                id: 0,
              },
              reference_string: 0,
              name: 0,
              priority: 0,
              status: 0,
              due_date: "date",
              description: 0,
              content_type: 0,
              model_id: 0,
              model_key: 0,
              created_by: {
                name: 0,
              },
              data: 0,
              assignee: {
                id: 0,
                name: 0,
                initials: 0,
                colour: 0,
              },
            },
          }),
        };
        $.ajax({
          method: "get",
          url: "/tasks/",
          data: data,
        }).then(
          function (result) {
            var tasks = helpers.get(result, "result.tasks");
            window.localStorage["tasklist_lastupdate"] = helpers.get(
              result,
              "result.lastupdate"
            );
            window.localStorage["tasklist_data"] = JSON.stringify({
              query: data.query,
              tasks: tasks,
            });
            resolve(tasks);
          },
          function (e) {
            debugger;
          }
        );
      });
    },
    getNwd: function () {
      var self = this;
      return new Promise(function (resolve, reject) {
        var tasks;
        // build a query
        var query = [
          { field: "case_id", value: "null" },
          { field: "status", value: "nwd" },
        ];
        if (!dit.user.is_admin) {
          _.each(helpers.get(self, "controller.sourceFilters", []), function (
            filter
          ) {
            switch (filter.field) {
              case "all_tasks":
                break;
              default:
                query.push({
                  field: filter.field,
                  value: filter.value,
                  combine: filter.combine,
                });
            }
          });
        }

        let data = {
          query: JSON.stringify(query),
          fields: JSON.stringify({
            Task: {
              id: 0,
              name: 0,
              status: 0,
              due_date: "date",
              data: 0,
              assignee: {
                id: 0,
                name: 0,
                initials: 0,
                colour: 0,
              },
            },
          }),
        };
        $.ajax({
          method: "get",
          url: "/tasks/",
          data: data,
        }).then(
          function (result) {
            var tasks = helpers.get(result, "result.tasks");
            _.each(tasks, function (nwDay) {
              nwDay.startDate = new Date(nwDay.data.start_date).round();
              nwDay.endDate = new Date(nwDay.due_date).round();
            });
            resolve(tasks);
          },
          function (e) {
            debugger;
          }
        );
      });
    },
  };
});
