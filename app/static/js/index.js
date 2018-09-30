$(function () {
    loadMessages();
});

function loadMessages() {
    $.ajax({
        url: '/api/messages',
        success: function (response) {
            let messages = response.messages;
            console.log(messages);
            let messageList = $('#message-list');
            messageList.empty();
            messageList.append(
                messages.map(message =>
                    `<li class='list-group-item message-item' data-seq-id='${message.sequence}' data-message-id='${message.id}'>
                        <div class="row">
                            <div class="col-md-10 col-sm-10">
                                <div class="col-md-3 col-sm-3">
                                    <i class="fa fa-phone"></i>
                                    ${message.phone_number.phone_number}
                                </div>
                                <div class="col-md-9 col-sm-9">
                                    <i class="fa fa-comment"></i>
                                    <input id="message-field-${message.id}" class="message-field" type="text" value="${message.message_text}" readonly/>
                                </div>
                            </div>
                            <div class="col-md-2 col-sm-2">
                                <button id="edit-${message.id}" type="submit" class="btn btn-default edit-btn">
                                    <i class="fa fa-pencil"></i> 
                                </button> 
                                <button id="delete-${message.id}" type="submit" class="btn btn-default delete-btn">
                                    <i class="fa fa-trash"></i> 
                                </button> 
                            </div>
                        </div>
                    </li>`
                )
            );
            messageList.sortable({
                start: function (event, ui) {
                    ui.item.startPos = ui.item.index();
                },
                stop: updateMessageSequence
            });
            messageList.disableSelection();

            $('.edit-btn').click(function () {
                let id = this.id.split('-')[1];
                let messageField = $(`#message-field-${id}`);
                messageField.attr('readonly', false);
            });

            $('.delete-btn').click(function () {
                let id = this.id.split('-')[1];
                deleteMessage(id);
            });

            $('.message-field').blur(function () {
                console.log(this);
                $(`${this.id}`).attr('readonly', true);
            });
        },
        error: function (response) {
        },

    });
}

function updateMessageSequence(event, ui) {
    let posChange = ui.item.index() - ui.item.startPos;
    let newSequence = parseInt(ui.item.attr('data-seq-id')) + posChange;
    console.log(posChange);
    console.log(newSequence);
    $.ajax({
        type: 'POST',
        url: '/api/update-message-sequence',
        contentType: 'application/json',
        data: JSON.stringify({
            "message_id": ui.item.attr('data-message-id'),
            "new_sequence": newSequence,
        }),
        success: function (response) {
            console.log(response);
        },
        error: function (response) {
        }
    });
}

function deleteMessage(id) {
    $.ajax({
        url: `/delete/message/${id}`,
        type: 'DELETE',
        success: function (response) {
            loadMessages();
        },
        error: function (response) {
            console.log(response);
        }
    })
}