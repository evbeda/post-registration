const $loginDiv = $('#login_div');
const $hideLoginDiv = $('#hide_login_div');
const $submitLogin = $('#submit_login');

const toggle = function () {
    $loginDiv.fadeToggle();
};

const toggleOut = function (event) {
	event.preventDefault();
};

const switcher = function () {
    $hideLoginDiv.on('click', toggle);
    $submitLogin.on('submit', toggleOut);
};

$(document).ready(switcher);