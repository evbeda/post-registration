const $managedEventsTag = $('#managed_events_tag');
const $evaluateEventsTag = $('#evaluate_events_tag');
const $manageEvents = $('#managed_events');
const $evaluateEvents = $('#evaluate_events');
const $ebUser = $('#eb_user');


const toggleManage = function () {
    $manageEvents.fadeIn();
    $evaluateEvents.hide();
    $managedEventsTag.addClass('active');
    $evaluateEventsTag.removeClass('active');

};

const toggleEvaluate = function () {
    $evaluateEvents.fadeIn();
    $manageEvents.hide();
    $managedEventsTag.removeClass('active');
    $evaluateEventsTag.addClass('active');
};

const switcher = function() {
 if ($ebUser.val() == 'True') {
   $manageEvents.show();
   $evaluateEvents.hide();
 } else {
   $evaluateEvents.show();
   $manageEvents.hide();
 }
 $managedEventsTag.on("click", toggleManage);
 $evaluateEventsTag.on("click", toggleEvaluate);
};

$(document).ready(switcher);
