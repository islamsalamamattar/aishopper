$(document).ready(function() {
    // Function to send message and update chat
    function sendMessage(message) {
        // Update chat with user message
        updatePrompt({ date: new Date().toLocaleString(), text: message });

        var token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJJc2xhbSIsImp0aSI6Ijc4NjYwNGE4LTJmM2EtNDA5MC05MTc0LTNjNmQ5ZmQyMTdkMSIsImlhdCI6MTcwOTUzNTgzNSwiZXhwIjoxNzA5NTQ2NjM1fQ.y_6HlQJNXiGjrgdKTEo3-JxzeCQYxpX1U18an4PKGBM"
        // API call
        $.ajax({
            url: '/api/chat/messages',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ prompt: message, token: token }),
            success: function(response) {
                // Update chat with response
                updateResponse(response);
            },
            error: function(xhr, status, error) {
                console.error('Error sending message:', error);
            }
        });
    }

    // Function to update chat with user prompt
    function updatePrompt(prompt) {
        var chatContainer = $('#chat-container');

        var listItem = $('<li>').addClass('widget-chat-date').text(prompt.date);
        chatContainer.append(listItem);

        listItem = $('<li>').addClass('prompt');
        var promptContainer = $('<div>').addClass('widget-list-container');
        promptContainer.append($('<div>').addClass('widget-list-media').html('<img src="/static/assets/img/user.jpg" alt="" />'));
        var promptContent = $('<div>').addClass('widget-list-content');
        promptContent.append($('<div>').addClass('widget-title').text('user'));
        promptContent.append($('<div>').addClass('widget-description').text(prompt.text));
        promptContainer.append(promptContent);
        listItem.append(promptContainer);
        chatContainer.append(listItem);

        // Scroll to bottom of chat
        chatContainer.scrollTop(chatContainer[0].scrollHeight);
    }

    // Function to update chat with response from API
    function updateResponse(response) {
        var chatContainer = $('#chat-container');

        var listItem = $('<li>').addClass('response');
        var responseContainer = $('<div>').addClass('widget-list-container');
        responseContainer.append($('<div>').addClass('widget-list-media').html('<img src="/static/assets/img/assistant.png" alt="" />'));
        var responseContent = $('<div>').addClass('widget-list-content');
        responseContent.append($('<div>').addClass('widget-title').text('Assistant'));
        responseContent.append($('<div>').addClass('widget-description').text(response));
        responseContainer.append(responseContent);
        listItem.append(responseContainer);
        chatContainer.append(listItem);

        // Scroll to bottom of chat
        chatContainer.scrollTop(chatContainer[0].scrollHeight);
    }

    // Event listener for send button click
    $('#send-button').click(function() {
        var message = $('#message-input').val().trim();
        if (message !== '') {
            sendMessage(message);
            // Clear input field after sending message
            $('#message-input').val('');
        }
    });

    // Initial chat update (optional)
    // sendMessage('Initial message');
});
