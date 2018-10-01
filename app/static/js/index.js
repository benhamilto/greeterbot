$(function () {
    loadMessages();
});

function loadMessages() {
    $.ajax({
        url: '/messages',
        success: function (response) {
            let messages = response.messages;
            let messageList = $('#message-list');
            messageList.empty();
            messageList.append(
                messages.map(message =>
                    `<li class='list-group-item message-item' data-seq-id='${message.sequence}' data-message-id='${message.id}'>
                        <div class="row vertical-align">
                            <div class="col-md-10 col-sm-10">
                                <div class="row">
                                    <div class="col-md-3 col-sm-3 phone-number">
                                        <i class="fa fa-phone"></i>
                                        ${message.phone_number.phone_number}
                                    </div>
                                    <div class="col-md-8 col-sm-8 comment">
                                        <i class="fa fa-comment"></i>
                                        <input id="message-field-${message.id}" class="message-field" type="text" value="${message.message_text}" readonly/>
                                    </div>
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
    $.ajax({
        type: 'POST',
        url: '/update/message-sequence',
        contentType: 'application/json',
        data: JSON.stringify({
            "message_id": ui.item.attr('data-message-id'),
            "new_sequence": newSequence,
        }),
        success: function (response) {
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
        }
    })
}