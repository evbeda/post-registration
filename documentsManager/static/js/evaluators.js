const $statusEvaluators = $('.badge.evaluators_states');
const $showEditBtn = $('#showEditBtn');
const $submitBtn = $('#submitBtn');
const $cancelBtn = $('#cancelBtn');
const $editForm = $('#editForm');
const $form = $('#evalPeriodForm');
const $datesView = $('#datesView');
const $warningDiv = $('#warning_div');
const $errorDiv = $('#error_div');


const toggleEditForm = () => {
    $editForm.toggleClass('d-none');
    $datesView.toggle('d-none');
}

const submitForm = (event) => {
    event.preventDefault();
    $form.submit();
}

const paint = function(index,element){
    const state = $(element).text();
    switch(state){
        case 'pending':
            $(element).addClass('badge-warning');
            break;
        case 'accepted':
            $(element).addClass('badge-success');
            break;
        case 'rejected':
            $(element).addClass('badge-danger');
            break;
        default:
            $(element).addClass('badge-dark');
            break;
    }
};

const switcher = function () {
    $statusEvaluators.each(paint);
    $showEditBtn.on('click', toggleEditForm);
    $submitBtn.on('click', submitForm);
    $cancelBtn.on('click', toggleEditForm);
};

$(document).ready(switcher);
