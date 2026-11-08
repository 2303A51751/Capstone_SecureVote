var selected;

$('#search').on('input', function(){
    var query = $('#search').val().toLowerCase();
    for (var party of parties_list_json) {
        var matchName = party.party_name.toLowerCase().includes(query);
        var matchCand = party.candidate_name ? party.candidate_name.toLowerCase().includes(query) : false;
        if (matchName || matchCand) {
            $('#' + party.party_id).css('display', 'flex');
        } else {
            $('#' + party.party_id).css('display', 'none');
        }
    }
});

// Auto-fill key button
$(document).off('click', '#auto-fill-key-btn').on('click', '#auto-fill-key-btn', function(e){
    e.preventDefault();
    if (typeof generated_voter_private_key !== 'undefined' && generated_voter_private_key) {
        $('#private-key-input').val(generated_voter_private_key);
        showAlert('ECDSA Private Key auto-filled.', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
    } else {
        showAlert('No key in session. Please paste manually.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
    }
});

// Download key button
$(document).off('click', '#download-key-btn').on('click', '#download-key-btn', function(e){
    e.preventDefault();
    var key = $('#private-key-input').val() || generated_voter_private_key;
    if (!key) {
        showAlert('No private key available to download.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
        return;
    }
    var blob = new Blob([key], { type: 'application/x-pem-file' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'voter_private_key.pem';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showAlert('Key downloaded as voter_private_key.pem', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
});

// When an option is clicked
$('.option').click(function(){

    if(selected){
        $(selected).find('.party-logo').css('width', '80px');
        $(selected).find('img').css({'width': '80px', 'height': '80px'});
        $(selected).find('.divider').show();
        $(selected).find('.party-name').css({'width': '300px', 'font-size': '20px'});
        $(selected).css({'flex-direction': 'row'});
        $(selected).children('.final-decision').remove();
    }

    selected = this;

    $(this).find('.party-logo').css('width', '140px');
    $(this).find('img').css({'width': '120px', 'height': '120px'});
    $(this).find('.divider').hide();
    $(this).find('.party-name').css({'width': '400px', 'font-size': '26px'});
    $(this).css({'flex-direction': 'column'});

    $(this).append("<div class='final-decision'><a id='vote' style='cursor:pointer;'>Select & Sign Ballot</a></div>");
    
    $('#vote').click(function(e){
        e.stopPropagation();
        showAlert('Review ballot and provide ECDSA signature.', 'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');
        $('.dialog').css('display', 'flex');
        $('.vote-confirmation').removeClass('confirmVoteDialoge-slide-fade-out');
        $('.vote-confirmation').addClass('confirmVoteDialoge-slide-fade-in');
        $('.confirmation-party-logo').attr('src', $(selected).find('img').attr('src'));
        $('.confirmation-party-name').html($(selected).find('.party-name div:first-child').html());

        // Pre-fill generated key by default for easy workflow
        if (typeof generated_voter_private_key !== 'undefined' && generated_voter_private_key && !$('#private-key-input').val()) {
            $('#private-key-input').val(generated_voter_private_key);
        }
    });
});

$('#final-confirm').click(function(){
    var selectedPartyID = $(selected).attr('id');
    var privateKey = $('#private-key-input').val().trim();

    if (!privateKey) {
        showAlert('Private Key is required to digitally sign the ballot!', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
        return;
    }

    showAlert('Cryptographically signing ballot with SHA3-256 and ECDSA...', 'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');
    $('.party-selection').remove();
    
    // Flash party logo and name for 2 sec
    $('.all-done').css('display', 'flex');
    $('.voted-party-image').attr('src', $(selected).find('img').attr('src'));
    $('.final-message').html('Your Vote:<br>' + $(selected).find('.party-name div:first-child').html());

    hideSelectedPartyLogo();

    $.ajax({
        type: 'POST',
        url: '/create-vote/',
        data: {
            'selected-party-id': selectedPartyID,
            'private-key': privateKey
        },
        success: function(data){
            $('.all-done').append(data.html);
            $('.all-done').addClass('all-done-rotate-collapse');

            showFinalStatus();

            if(data.success) {
                showAlert('Vote sealed in mempool with valid digital signature!', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                $('.final-status-row:nth-child(3)').find('td:last-child').css('color', 'rgb(0, 128, 0)');
            }
            else {
                showAlert(data.status || 'Signature verification failed!', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        },
        error: function(err) {
            showAlert('Failed to submit vote to blockchain network.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
        }
    });

});

$('#cancel-confirm').click(function(){
    showAlert('Ballot signing canceled.', 'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');
    $('.vote-confirmation').removeClass('confirmVoteDialoge-slide-fade-in');
    $('.vote-confirmation').addClass('confirmVoteDialoge-slide-fade-out');
    setTimeout(function(){
        $('.dialog').css('display', 'none');
    }, 500);
});

function hideSelectedPartyLogo(){
    $('.selected-party').animate({
        'opacity': '0'
    }, 1500);

    setTimeout(function(){
        $('.selected-party').animate({
            'height': '0',
            'width': '0',
        }, 800);
        setTimeout(function(){
            $('.selected-party').remove();
        }, 800);
    }, 1500);
}

function showFinalStatus() {
    setTimeout(function(){
        $('.front').hide();
        $('.final-status-container').show();
        $('.all-done').removeClass('all-done-rotate-collapse');
        $('.all-done').addClass('all-done-rotate-expand');
    }, 400);
}
