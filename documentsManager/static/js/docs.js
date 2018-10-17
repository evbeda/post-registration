const event_start = moment($('#eb_event_start').val(), 'YYYY-MM-DDTH:mm:ssZ');
const $allowEdit = $('#allow_edit');
const $allowEditDiv = $('#allow_edit_div');
const $confirmEdit = $('#confirm_edit');
const $cancelEdit = $('#cancel_update');
const $confirmEditDiv = $('#confirm_edit_div');
const $confirmEditWarning = $('#confirm_edit_warning');
const $cancelEditWarning = $('#cancel_update_warning');
const $warningDiv = $('#warning_div')
const $cancelEditError = $('#cancel_update_error');
const $errorDiv = $('#error_div')
const $inputEndSubmission = $('#id_end_submission');
const $inputInitSubmission = $('#id_init_submission');
const $textModal = $('#modal-body-warning');
const $formulario = $('#dates_form');

const toggleFormsEdit = function () {
    $allowEditDiv.fadeOut('fast', () => $confirmEditDiv.fadeIn());
    $inputEndSubmission.attr('min', $inputInitSubmission.val());
};

const hideInputs = function (value) {
    $inputEndSubmission.prop('disabled', value);
    $inputInitSubmission.prop('disabled', value);
}

const hideEditButton = function () {
    $confirmEdit.hide();
    $cancelEdit.hide();
}

const hideWarningErrorButton = function () {
    $confirmEditWarning.hide();
    $cancelEditWarning.closest('span').hide();
    $cancelEditError.closest('span').hide();
}

const confirmForm = function(event) {
    event.preventDefault();
    const date_init_is_before = event_start.isBefore($inputInitSubmission.val());
    const date_end_is_before = event_start.isBefore($inputEndSubmission.val());
    if (moment($inputEndSubmission.val()).isBefore($inputInitSubmission.val())) {
        $errorDiv.fadeIn();
        hideEditButton();
        $cancelEditError.closest('span').show();
        hideInputs(true);
        $errorDiv.find('.alert').text('The end date is greater than the start date of the submissions.')
    }
    else if (date_init_is_before || date_end_is_before) {
            $warningDiv.fadeIn();
            hideEditButton();
            $confirmEditWarning.show();
            $cancelEditWarning.closest('span').show();
            hideInputs(true);
        if (date_end_is_before && date_init_is_before) {
            $warningDiv.find('.alert').text('The end and start date is greater than the start date of the event.')
        }
        else if (date_end_is_before) {
            $warningDiv.find('.alert').text('The end date is greater than the start date of the event.')
        }
    } else {
        $formulario.submit();
    }
};

const confirmFormWarning = function (event) {
    event.preventDefault();
    hideInputs(false);
    $formulario.submit();
}

const cancelEdition = function (event) {
    event.preventDefault();
    $confirmEditDiv.fadeOut('fast', () => $allowEditDiv.fadeIn());
    $confirmEdit.fadeIn('fast');
    $cancelEdit.fadeIn('fast');
    hideInputs(false);
};

const backToEdit = function (event) {
    event.preventDefault();
    $confirmEdit.fadeIn('fast');
    $cancelEdit.fadeIn('fast');
    $warningDiv.hide();
    $errorDiv.hide();
    hideWarningErrorButton();
    hideInputs(false);
};

const switcher = function () {
    $confirmEditDiv.hide();
    $warningDiv.hide();
    $errorDiv.hide();
    hideWarningErrorButton();
    $allowEdit.on('click', toggleFormsEdit);
    $confirmEdit.on('click', confirmForm);
    $cancelEdit.on('click', cancelEdition);
    $confirmEditWarning.on('click', confirmFormWarning);
    $cancelEditWarning.on('click', backToEdit);
    $cancelEditError.on('click', backToEdit);
};

$(document).ready(switcher);
