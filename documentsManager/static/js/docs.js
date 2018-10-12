const event_start = moment($('#eb_event_start').val(), 'YYYY-MM-DDTH:mm:ssZ');
const $allowEdit = $('#allow_edit');
const $confirmEdit = $('#confirm_edit');
const $allowEditDiv = $('#allow_edit_div');
const $confirmEditDiv = $('#confirm_edit_div');
const $inputEndSubmission = $('#id_end_submission');
const $inputInitSubmission = $('#id_init_submission');
const $cancelUpdate = $('#cancel_update');
const $buttonSaveWarningDates = $('#save_warning_dates');
const $textModal = $('#modal-body-warning');
const $formulario = $('#dates_form');

const toggleFormsEdit = function () {
    $allowEditDiv.fadeOut('fast', () => $confirmEditDiv.fadeIn());
    $inputEndSubmission.attr('min', $inputInitSubmission.val());
};

const confirmForm = function (event) {
    $buttonSaveWarningDates.show();
    event.target.checkValidity();
    event.preventDefault();
    const date_init_is_before = event_start.isBefore($inputInitSubmission.val());
    const date_end_is_before = event_start.isBefore($inputEndSubmission.val());
    if (moment($inputEndSubmission.val()).isBefore($inputInitSubmission.val())) {
        $buttonSaveWarningDates.hide();
        $textModal.text('The end date is greater than the start date of the submissions.');
        $('#myModal').modal('show');
    }
    if (date_init_is_before || date_end_is_before) {
        if (date_end_is_before && date_init_is_before) {
            $textModal.text('The end and start date is greater than the start date of the event.');
        }
        else if (date_end_is_before) {
            $textModal.text('The end date is greater than the start date of the event.');
        }
        $('#myModal').modal('show');
    } else {
        $formulario.submit();
    }
};

const cancelEdition = function (event) {
    event.preventDefault();
    $confirmEditDiv.fadeOut('fast', () => $allowEditDiv.fadeIn());
};

const saveWarningDates = function () {
    $formulario.submit();
};
const switcher = function () {
    $confirmEditDiv.hide();
    $allowEdit.on('click', toggleFormsEdit);
    $confirmEdit.on('click', confirmForm);
    $cancelUpdate.on('click', cancelEdition);
    $buttonSaveWarningDates.on('click', saveWarningDates);
};

$(document).ready(switcher);
