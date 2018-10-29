const $buttonSubmission = $('#sub_button');
const $textForms = $('.text_area_form');

const checkLimits = function(i,e){
    const $elemento = $(e);
    const measure = $elemento.find('.measure').val();
    const min = parseInt($elemento.find('.min').val());
    const max = parseInt($elemento.find('.max').val());
    const texto = $elemento.find('textarea').removeClass('is-invalid');
    let quantity = texto.val().length;
    if (measure === 'Words'){
        quantity = texto.val().split(' ').length;
    }
    if (min > quantity && quantity < max){
        const html =`
        <small class="text-danger">
            You have errors. Allowed ${min} - ${max} ${measure}
        </small>
        `;
        texto.addClass('is-invalid').after(html);
    }
};

const validateForm = function(e){
    e.preventDefault();
    $textForms.find('small').remove();
    $textForms.each(checkLimits);
    const validations = document.getElementById('submission_form').reportValidity();
    if (validations && $('.is-invalid').length == 0 ){
        $('form').submit();
    }
};

const init =  function (){
    $buttonSubmission.on('click',validateForm);
};

$(document).ready(init);
