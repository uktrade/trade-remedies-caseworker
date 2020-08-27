define([
  "modules/helpers",
  "widgets/tasks/TaskData",
  "modules/Events",
], function (helpers, taskData, Events) {
  "use strict";

  var millisPerDay = 1000 * 60 * 60 * 24;
  var splitBlocks = true;

  var templateStrings = {
    dateScale: `
            <div class="date-scale" style="width:<%=((obj.scaleX || []).length * 44)+'px;'%>">
                <div class="day-scale">
                    <% for(var idx=0; idx<(obj.scaleX || []).length;idx++) { %><div style="left:<%=obj.scaleX[idx].x %>%;"><%=obj.scaleX[idx].label%></div><% } %>
                </div>
            </div>
        `,
    calendar: `
            <div class="person-scale" data-attach="ScrollShadow">
                <%=obj.personScale%>
            </div>
            <div class="accumulate-box">
                <div class="multiple-choice tiny pull-left">
                    <input value="done" type="checkbox" id="accumulate" name="cal_accumulate" <% if(helpers.get(obj,'self.controller.settings.cal_accumulate')) print('checked="checked"') %>>
                    <label class="form-label">
                        &#931;
                    </label>
                </div>
            <!-- <label>&#931;<input type="checkbox" id="accumulate" name="cal_accumulate" <% if(helpers.get(obj,'self.controller.settings.cal_accumulate')) print('checked="checked"') %>></label> -->
            </div>
            <div class="calendar" data-attach="ScrollShadow" >
                <div class="day-scale" style="width:<%=((obj.weeks || []).length * 35 * 7)+'px;'%>">
                    <% for(var idx=0; idx<(obj.weeks || []).length;idx++) { var week = obj.weeks[idx];
                    %><div><div class="week-header"><%=week.label%></div>
                        <% for(var dayIdx=0; dayIdx<week.days.length ; dayIdx++) { var day = week.days[dayIdx] %>
                            <div class="day <% if(day.nwd) print('weekend'); %> <% if(day.today) print('today'); %>" <%if(day.nwd && day.nwd.name) print('title="'+day.nwd.name+'"')%>><%=day.label%></div>
                        <% } %>
                    </div>
                    <% } %>
                </div>

                <div class="calendar-body" data-attach="ScrollShadow">
                    <div style="width:<%=((obj.weeks || []).length * 35 * 7)+'px;'%>height:100%;">
                    <%=obj.body %>
                    </div
                </div>
            </div>
        `,
    personScale: `
            <% for(var idxa=0; idxa<obj.assignees.length; idxa++) { var rec = obj.assignees[idxa]; %>
                <div class="person-label" style="height:<%=Math.round(80/obj.assignees.length)%>%">
                <% if(!rec.assignees) { print(obj.self.controller.templates.userBadge(rec.assignee || {})); } else {
                    %><div class="assignee-list"><%
                    for(var idx=0; idx< rec.assignees.length; idx++) {
                        print(obj.self.controller.templates.userBadge(rec.assignees[idx].assignee || {}));
                    }
                    %></div><%
                } %>
                    <% if(rec.overdue) { %>
                        <div class="overdue circular-badge small" title="<%=rec.overdue.points %> points overdue"><%=rec.overdue.points %></div>
                    <% } %>
                </div>
            <% } %>
        `,
    calendarBody: `
            <% for(var idxa=0; idxa<obj.assignees.length; idxa++) { var rec = obj.assignees[idxa]; %>
                <div class="person-graph" style="height:<%=Math.round(80/obj.assignees.length)%>%" >
                    <% for(var idx=0;idx<rec.blocks.length; idx++) { var block=rec.blocks[idx]; %>
                        <div class="block" style="left:<%=block.left%>px;width:<%=block.width%>px;">
                            <% if(block.peak) {%>
                                <div style="height:<%=100*block.peak/obj.maxPoints%>%;background-color:<%=(rec.assignee && rec.assignee.colour) || '#888;'%>;">
                                <span class="<% if(block.peak/obj.maxPoints > 0.3) print('high'); %>"><%=Math.round(block.peak*10)/10%><%= block.width < 40 ? '' : (block.width < 80 ? '&nbsp;pt/dy' : '&nbsp;pts/day') %></span>
                                </div>
                            <% } else { %>
                                <div class="non-working">
                                <span title="<%=block.name%>"><%=block.name%></span>
                                </div>
                            <% } %>
                        </div>
                    <% } %>
                </div>
            <% } %>
        `,
  };

  function constructor(controller, container) {
    this.controller = controller;
    this.$gridContainer = container;
    this.templates = {};
    _.bindAll(this, "onScroll", "onChange");
    this.$gridContainer.on("change", this.onChange);
    _.each(
      templateStrings,
      function (str, key) {
        this.templates[key] = _.template(str, { variable: "obj" });
      },
      this
    );
  }

  function sortFn(field, rev) {
    if (rev) {
      return function (a, b) {
        var A = a[field],
          B = b[field];
        return A == B ? 0 : A < B ? 1 : -1;
      };
    }
    return function (a, b) {
      var A = a[field],
        B = b[field];
      return A == B ? 0 : A < B ? -1 : 1;
    };
  }

  function buildValueScale(max, maxDivisions) {
    // not used ATM, but may be useful
    var div = Math.pow(
      10,
      Math.ceil(Math.log(max / maxDivisions) / Math.log(10))
    );
    div = _.reduce(
      [2, 5],
      function (memo, val) {
        return (max * val) / div < maxDivisions ? div / val : memo;
      },
      div
    );
    var scale = [];
    if (div > 0) {
      for (var grad = 0; grad <= max; grad += div) {
        var label = "" + Math.round(grad * 10) / 10; // clean rounding errors
        scale.push({ y: (100 * grad) / max, label: label });
      }
    }
    return scale;
  }

  constructor.prototype = {
    onChange: function (evt) {
      var target = $(evt.target);
      if (target.attr("id") == "accumulate") {
        var settings = {};
        settings[target.attr("name")] = target.is(":checked");
        this.controller.saveSettings(settings);
        new Events().fire("tasks_updated");
      }
    },

    isNwDay(date, assigneeId) {
      var isWeekend = date.getDay() in { 0: 1, 6: 1 };
      if (isWeekend) {
        return true;
      }
      var nwDays = this.nwdMap[""] || [];
      if (assigneeId) {
        nwDays = nwDays.concat(this.nwdMap[assigneeId]);
      }
      for (var index = 0; index < nwDays.length; index++) {
        var nwPeriod = nwDays[index];
        if (nwPeriod.startDate <= date) {
          if (nwPeriod.endDate >= date) {
            return nwPeriod;
          }
        }
      }
    },

    getWorkingDays: function (startDate, maxDays, assigneeId) {
      var out = {};
      var dayCount = 0;

      for (var idx = 0; idx < maxDays; idx++) {
        var date = new Date(startDate.getTime() + idx * millisPerDay);
        var isNwDay = this.isNwDay(date, assigneeId);
        if (!isNwDay) {
          dayCount++;
        }
        out[date.format("yyyy-mm-dd")] = {
          count: dayCount,
          weekend: isNwDay,
          day: date.getDay(),
        };
      }
      return out;
    },

    calcWorkload: function (startDate, tasks, workingDayMap) {
      tasks.sort(sortFn("due_date"));
      var overdue = [];
      var peaks = [];
      var peakIdx = -1;
      var peakWd = 0;
      while (tasks.length && peakIdx + 1 < tasks.length) {
        let runningTotal = 0;
        let peak = 0;
        for (var idx = peakIdx + 1; idx < tasks.length; idx++) {
          var task = tasks[idx];
          if (task.due_date) {
            var dueDate = new Date(task.due_date);
            var remaining = parseInt(helpers.get(task, "data.remaining"));
            if (_.isNaN(remaining)) {
              remaining = parseInt(helpers.get(task, "data.estimate"));
            }
            remaining = remaining || 0;
            task.remaining = remaining;
            var workingDays = workingDayMap[dueDate.format("yyyy-mm-dd")];
            if (workingDays) {
              if (workingDays.count <= peakWd) {
                overdue.push(task);
              } else {
                runningTotal += remaining || 0;
                var runningPeak = runningTotal / (workingDays.count - peakWd);
                var taskStart = helpers.get(task, "data.start_date");
                if (taskStart) {
                  var taskStartDate = new Date(taskStart.substring(0, 10));
                  var daysToDo = (dueDate - taskStartDate) / millisPerDay + 1;
                  var taskPeak = remaining / daysToDo;
                  runningPeak = Math.max(runningPeak, taskPeak);
                }
                if (runningPeak >= peak) {
                  peak = runningPeak;
                  peakIdx = idx;
                }
              }
            } else {
              if (task.due_date < new Date().format("yyyy-mm-dd")) {
                // this is so we dont include tasks that are way in the future and not in the working-day map
                overdue.push(task);
              }
            }
          }
        }
        if (peak) {
          var endDate = new Date(tasks[peakIdx].due_date);
          if (splitBlocks) {
            // break the block into bits around NWDs
            var dt = new Date(startDate);
            var blockStart, blockEnd;
            while (dt <= endDate) {
              var wd = workingDayMap[dt.format("yyyy-mm-dd")];
              if (!wd.weekend) {
                blockStart = blockStart || dt;
                blockEnd = dt;
              }
              if (wd.weekend || dt >= endDate) {
                if (blockStart) {
                  peaks.push({
                    startDate: blockStart,
                    endDate: blockEnd,
                    peak: peak,
                  });
                  blockStart = null;
                }
              }
              dt = dt.addDays(1);
            }
          } else {
            peaks.push({
              startDate: startDate, //fix
              endDate: endDate,
              peak: peak,
            });
          }

          startDate = endDate.addDays(1);
          peakWd = workingDayMap[endDate.format("yyyy-mm-dd")].count;
        } else {
          break;
        }
      }
      return {
        peaks: peaks,
        overdue: overdue,
      };
    },

    onScroll: function (evt) {
      this.scrollSlave.css({ "margin-left": 0 - evt.target.scrollLeft + "px" });
      this.scrollSlaveY[0].scrollTop = evt.target.scrollTop;
    },

    getCalendarInner: function (tasks, startDate, calcStartDate) {
      var self = this;
      var dayWidth = 35; // pixel width of one day;
      var body = "",
        personScale = "";
      var assignees = {};
      _.each(tasks, function (task) {
        var id = (task.assignee || {}).id || "unassigned";
        assignees[id] = assignees[id] || { assignee: task.assignee, tasks: [] };
        assignees[id].tasks.push(task);
      });
      // If we are in accumulate mode and there is only one assignee - we're ok.  Otherwise blat it.
      if (this.accumulate && _.keys(assignees).length > 1) {
        assignees = {
          all: {
            tasks: tasks,
            assignees: _.values(assignees),
          },
        };
      }

      var workingDayMap = self.getWorkingDays(calcStartDate, 60);

      var maxPoints = 0;
      _.each(assignees, function (rec, id) {
        var locWorkingDayMap = self.nwdMap[id]
          ? self.getWorkingDays(calcStartDate, 60, id)
          : workingDayMap;
        // get the workload projection for this set of tasks
        var workload = self.calcWorkload(
          calcStartDate,
          rec.tasks,
          locWorkingDayMap
        );
        var innerMaxPoints = 0;
        // Add in any personal NW days
        var wlMap = workload.peaks.concat(self.nwdMap[id] || []);
        // generate a set of blocks from this, adding in the lefts and widths of the blocks
        _.each(wlMap, function (block) {
          block.left =
            ((block.startDate.getTime() - startDate.getTime()) * dayWidth) /
            millisPerDay;
          block.width =
            (1 +
              (block.endDate.getTime() - block.startDate.getTime()) /
                millisPerDay) *
            dayWidth;
          innerMaxPoints = Math.max(innerMaxPoints, block.peak || 0);
        });
        rec.blocks = wlMap;
        if (workload.overdue.length) {
          var overduePoints = 0;
          _.each(workload.overdue, function (task) {
            overduePoints += task.remaining;
          });
          rec.overdue = { points: overduePoints };
        }
        rec.maxPoints = innerMaxPoints;
        maxPoints = Math.max(innerMaxPoints, maxPoints);
      });
      var data = {
        assignees: _.values(assignees).sort(sortFn("maxPoints", true)),
        maxPoints: maxPoints,
        self: self,
      };
      return {
        body: self.templates.calendarBody(data),
        scale: self.templates.personScale(data),
        plotCount: _.keys(assignees).length,
      };
    },

    renderCalendar: function (tasks) {
      var self = this;
      var now = new Date();
      this.accumulate = helpers.get(self, "controller.settings.cal_accumulate");
      var startDate = new Date(now.format("yyyy-mm-dd"));
      var calcStartDate = new Date(startDate);
      var endDate = startDate.addDays(60);
      // calculate week start
      startDate = new Date(
        startDate.getTime() - startDate.getDay() * millisPerDay
      ).addDays(1);

      taskData.getNwd().then(function (nwDays) {
        self.nwdMap = helpers.index(nwDays, "assignee.id");
        var weekScale = [];
        for (var week = 0; week < 8; week++) {
          var weekStart = new Date(
            startDate.getTime() + week * 7 * millisPerDay
          );
          var weekEnd = weekStart.addDays(6);
          var days = [];
          for (var idx = 0; idx < 7; idx++) {
            var date = weekStart.addDays(idx);
            days.push({
              nwd: self.isNwDay(date),
              today: date.getTime() == calcStartDate.getTime(),
              label: date.format("day"),
            });
          }
          weekScale.push({
            startDate: weekStart,
            endDate: weekEnd,
            label: `${weekStart.format("dd mon")} to ${weekEnd.format(
              "dd mon"
            )}`,
            days: days,
          });
        }

        var inner = self.getCalendarInner(tasks, startDate, calcStartDate);
        self.$gridContainer.setClass("single-graph", inner.plotCount == 1);
        self.$gridContainer.html(
          self.templates.calendar({
            weeks: weekScale,
            body: inner.body,
            personScale: inner.scale,
            self: self,
          })
        );
        self.$gridContainer.find(".calendar-body").on("scroll", self.onScroll);
        self.scrollSlave = self.$gridContainer.find(".day-scale");
        self.scrollSlaveY = self.$gridContainer.find(".person-scale");
        self.$gridContainer.attachWidgets();
      });
    },
  };
  return constructor;
});
