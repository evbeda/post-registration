const $statusEvaluators = $('.badge.evaluators_states');

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
};

$(document).ready(switcher);
