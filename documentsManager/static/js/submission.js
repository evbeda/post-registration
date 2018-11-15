const $informationNav = $('#information-nav');
const $reviewsNav = $('#reviews-nav');
const $evaluatorsNav = $('#evaluators-nav');
const $informationDiv = $('#information-div');
const $reviewsDiv = $('#reviews-div');
const $evaluatorsDiv = $('#evaluators-div');

const infoActivateAndToggle = function () {
    $evaluatorsNav.removeClass('active');
    $reviewsNav.removeClass('active');
    $informationNav.addClass('active');
    $reviewsDiv.hide();
    $evaluatorsDiv.hide();
    $informationDiv.show();
};

const reviewActivateAndToggle = function () {
    $evaluatorsNav.removeClass('active');
    $informationNav.removeClass('active');
    $reviewsNav.addClass('active');
    $informationDiv.hide();
    $evaluatorsDiv.hide();
    $reviewsDiv.show();
};

const evalActivateAndToggle = function () {
    $reviewsNav.removeClass('active');
    $informationNav.removeClass('active');
    $evaluatorsNav.addClass('active');
    $reviewsDiv.hide();
    $informationDiv.hide();
    $evaluatorsDiv.show();
};

const switcher = function () {
    $reviewsDiv.hide();
    $evaluatorsDiv.hide();
    $informationDiv.show();
    $informationNav.on('click', infoActivateAndToggle);
    $reviewsNav.on('click', reviewActivateAndToggle);
    $evaluatorsNav.on('click', evalActivateAndToggle);
};

$(document).ready(switcher);