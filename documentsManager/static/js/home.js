const $managedEventsTag = $('#managed_events_tag');
const $evaluateEventsTag = $('#evaluate_events_tag');
const $manageEvents = $('#managed_events');
const $evaluateEvents = $('#evaluate_events');


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

const switcher = function () {
    $evaluateEvents.hide();
    $manageEvents.show();
    $managedEventsTag.on('click', toggleManage);
    $evaluateEventsTag.on('click', toggleEvaluate);
};

$(document).ready(switcher);
