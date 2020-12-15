const confirm = async (event) => {
    event.preventDefault();

    const target = event.target
    const modal = document.querySelector('#staticBackdrop');
    const content = modal.querySelector('.modal-content');

    // Clear previous content
    content.innerHTML = null; 

    const action = target.attributes['data-action'].value;
    const formAction = action === 'buy' ? 'buy' : 'sell';

    let qty = 1;
    if (target.attributes.hasOwnProperty('data-qty')) {
        qty = target.attributes['data-qty'].value * 1;
    }
    const symbol = target.attributes['data-symbol'].value;

    let stockPrice = target.attributes['data-price'].value * 1;
    // --------- FIX THIS TO BE DYNAMIC ------ make API call only for freeFunds detail
    //const freeFunds = await fetch()
    let max = action === 'buy' ? Math.floor(99999 / stockPrice) : qty;

    // MODAL FORM ELEMENTS
    const form = document.createElement('form');
    form.action = `/${formAction}`;

    symbolAtts =  {'type': 'text', 'name': 'symbol', 'value': symbol, 'required': true, 'disabled': true};
    let value = action === 'buy' ? 1 : qty;
    qtyAtts = {'type': 'number', 'name': 'qty', 'value': value, 'required': true, 'step': 1, 'min': 1, 'max': max};
    if (action === 'close') {
        qtyAtts.disabled = true;
    }
    
    const symbolInputGroup = createFormGroup('symbol', 'Instrument', symbolAtts);
    const qtyInputGroup = createFormGroup('qty', 'Quantity', qtyAtts);

    const submitBtn = document.createElement('button');
    submitBtn.className = 'btn btn-primary';
    submitBtn.innerText = 'Confirm';

    submitBtn.onclick = (event) => {
        event.preventDefault();
        
        const alert = event.target.parentElement.previousElementSibling.children[2];
        const form = event.target.parentElement.parentElement;
        let q = form.action + '?';

        const inputs = form.querySelectorAll('input');
        const inputsLenght = inputs.length;
        
        let error = false;

        inputs.forEach((curr, i) => {
            if (!curr.validity.valid) {
                error = true;
            }

            const name = curr.attributes['name'].value;
            const value = curr.attributes['value'].value;
            q += name + '=' + value;
            if (i < inputsLenght - 1) {
                q += '&';
            }
        });

        if (error) {
            alert.innerHTML = `<div class="alert alert-danger" role="alert">Incorrect value!</div>`
            return;
        }

        async function postData(url = '', data = {}) {
            event.target.previousElementSibling.setAttribute('disabled', true);
            event.target.setAttribute('disabled', true);
            event.target.innerHTML = '<span class="spinner-border spinner-border-sm" ' +
                                     'role="status" aria-hidden="true"></span>&nbsp;Processing...'


            const response = await fetch(url, {
                method: 'POST', 
                headers: {
                'Content-Type': 'application/json'
                },
            });

            try {
                const data = await response.json();
            
                if (data.error) {
                    throw new Error(data.error);
                }

                alert.innerHTML = `<div class="alert alert-success" role="alert">${data.msg}!</div>`;
                event.target.innerHTML = 'Done!&nbsp;<i class="fas fa-check"></i>'

                setTimeout(() => {
                    // Hide modal
                    $('#staticBackdrop').modal('hide');
                    //Clear content
                    content.innerHTML = null;
                    // Update dashboard data
                    try {
                        update();
                    } catch (error) {
                        // bad design
                        // silent error when calling this from other url than dashboard
                    }
                }, 3000);
                

            } catch (error) {
                alert.innerHTML = `<div class="alert alert-danger" role="alert">${error}!</div>`;
                event.target.previousElementSibling.disabled = false;
                event.target.disabled = false;
                submitBtn.innerText = action[0].toUpperCase() + action.slice(1);
            }     
        }

        postData(q);

    }

    // MODAL HEADER
    const header = document.createElement('div');
    header.className = 'modal-header';
    const badgeColor = action === 'buy' ? 'success' : 'danger';
    header.innerHTML = `
        <h5 class="modal-title" id="staticBackdropLabel">
            <span class="badge badge-${badgeColor} mr-2">${action.toUpperCase()}</span> ${symbol} @ ${stockPrice}
        </h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `

    // MODAL ALERT
    const alert = document.createElement('div');

    // MODAL BODY
    const body = document.createElement('div');
    body.className = 'modal-body';
    
    body.append(symbolInputGroup);
    body.append(qtyInputGroup);
    body.append(alert);
    
    // MODAL FOOTER
    const footer = document.createElement('div');
    footer.className = 'modal-footer';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-secondary';
    cancelBtn.innerText = 'Cancel';
    cancelBtn.setAttribute('type', 'button');
    cancelBtn.setAttribute('data-dismiss', 'modal');

    footer.append(cancelBtn);
    footer.append(submitBtn);

    // PARSING
    form.append(body);
    form.append(footer);
    
    content.append(header);
    content.append(form);
    
    $('#staticBackdrop').modal('show');

}

const onChangeHandler = (event) => {
    event.target.setAttribute('value', event.target.value);
}

const createFormGroup = (id, text, attributes) => {
    const div = document.createElement('div');
    div.className = 'form-group';

    const label = document.createElement('label');
    label.setAttribute('for', id);
    label.innerText = text;

    const input = document.createElement('input');
    input.setAttribute('id', id);
    input.addEventListener('change', onChangeHandler);
    
    for (const [key, value] of Object.entries(attributes)) {
        input.setAttribute(key, value);
    }
    
    div.append(label);
    div.append(input);

    if (attributes.hasOwnProperty('max')) {
        const max = document.createElement('small');
        max.innerText = 'Max: ' + attributes.max;
        div.append(max);
    }

    return div;
}

