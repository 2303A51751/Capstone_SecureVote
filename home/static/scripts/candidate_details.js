var emailmsg1 = 'Please enter a valid Email-ID and verify it. Key will be sent to this Email-ID.';
var emailmsg2 = 'Click "Send OTP" to receive your one-time verification passcode.';
var valid_email_pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
var generated_voter_private_key = "";

$(document).ready(function(){
    
    $('.email-alert-msg').addClass('email-alert-msg-slide-fade-in');
    set_email_alert_msg();

    function set_email_alert_msg(){
        if( valid_email_pattern.test($('#email-input').val()) ){
            $('.email-alert-msg').html(emailmsg2);
        }
        else{
            $('.email-alert-msg').html(emailmsg1);
        }
    }

    // Email validation on input
    $('#email-input').on('input', function(){
        set_email_alert_msg();
    });

    // Show or hide input div on button click
    $('#change-email').click(function(){
        if( $(this).html() == 'Change' ){
            $('#email-input').prop('disabled', false);
            $('#email-input').removeClass('email-input');
            $('#email-input').css({'color': 'black', 'text-align': 'left'});
            $(this).html('Done');
            
            $('#send-otp').show();
            $('#verified-badge').hide();
            $('#vote-now').addClass('disabled');
            $('.email-alert-msg').show();
        }
        else{
            $('#email-input').prop('disabled', true);
            $('#email-input').addClass('email-input');
            $('#email-input').css('color', 'white');
            $(this).html('Change');
        }
    });

    // Send otp to email address on button click and display verification div
    $('#send-otp').click(function(){

        if( valid_email_pattern.test($('#email-input').val()) ){
        
            if($('#change-email').html()=='Done'){
                $('#email-input').prop('disabled', true);
                $('#email-input').addClass('email-input');
                $('#email-input').css('color', 'white');
                $('#change-email').html('Change');
            }

            show_loading('Sending OTP to ' + $('#email-input').val() + '...');

            $.ajax({
                type:'POST',
                url: '/send-otp/',
                data: {'email-id': $('#email-input').val()},
                success: function(data){
                    setTimeout(function(){
                        hide_loading_without_reload();
                    }, 800);

                    if(data.success){
                        $('.otp-div').removeClass('otp-verification-slide-to-bottom');
                        $('.otp-div').addClass('otp-verification-slide-from-bottom');
                        $('#otp-verfication-email').html($('#email-input').val());
                        
                        // Auto-fill in demo mode; in live mode wait for voter to enter from inbox
                        if (data.otp) {
                            $('#otp-input').val(data.otp);
                            $('#otp-demo-hint').html('Demo Mode: OTP auto-filled (' + data.otp + '). Click "Verify OTP".');
                            showAlert('OTP: ' + data.otp + ' (Auto-filled for demo testing)', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                        } else {
                            $('#otp-input').val('').focus();
                            $('#otp-demo-hint').html('Live Delivery: Please check registered email inbox (' + $('#email-input').val() + ') for the OTP code.');
                            showAlert('OTP sent to ' + $('#email-input').val() + '. Please check your inbox!', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                        }

                        $('.otp-verification').show();
                        $('.otp-div').show();
                    }
                    else {
                        showAlert(data.error || 'Failed to send OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                    }
                },
                error: function(err) {
                    hide_loading_without_reload();
                    showAlert('Network error sending OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            });

        }
        else {
            $('.email-alert-msg').removeClass('email-alert-msg-slide-fade-in');
            $('.email-alert-msg').addClass('boom');
            setTimeout(function(){
                $('.email-alert-msg').removeClass('boom');
            }, 1000);
        }
    });

    // Verify OTP by entered OTP
    $('#verify').click(function(){

        var code = $('#otp-input').val().trim();
        if(!code){
            showAlert('Please enter the OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            return;
        }

        show_loading('Verifying OTP code...');

        $.ajax({
            type:'POST',
            url: '/verify-otp/',
            data: {'otp-input': code},
            success: function(data){
                setTimeout(function(){
                    hide_loading_without_reload();
                }, 600);

                if(data.success){
                    $('.otp-div').removeClass('otp-verification-slide-from-bottom');
                    $('.otp-div').addClass('otp-verification-slide-to-bottom');
                    setTimeout(function(){
                        $('.otp-verification').hide();
                        $('.otp-div').hide();
                    }, 500);

                    $('#send-otp').hide();
                    $('#verified-badge').css('display', 'inline');
                    $('#email-input').css('text-align', 'right');
                    $('#vote-now').removeClass('disabled');
                    $('.email-alert-msg').hide();
                    
                    showAlert('Email Verified! You are now authorized to vote.', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                }
                else {
                    showAlert(data.error || 'Invalid OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            },
            error: function() {
                hide_loading_without_reload();
                showAlert('Verification request failed.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

    // Cancel OTP verification
    $('#cancel-otp').click(function(){
        $('.otp-div').removeClass('otp-verification-slide-from-bottom');
        $('.otp-div').addClass('otp-verification-slide-to-bottom');
        setTimeout(function(){
            $('.otp-verification').hide();
            $('.otp-div').hide();
        }, 500);
    });

    // Support Enter in OTP input
    $('#otp-input').on('keypress', function(e){
        if(e.which === 13) {
            $('#verify').click();
        }
    });

    // Proceed to Vote
    $('#vote-now').click(function(event){
        if($(this).hasClass('disabled')) return;

        show_loading('Generating NIST P-256 Elliptic Curve Keypair...');

        $.ajax({
            type:'GET',
            url: '/get-parties/',
            success: function(data){
                if (data.error) {
                    hide_loading();
                    showAlert(data.error, 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                    return;
                }

                parties_list_json = data.parties;
                // Store private key for UI quick paste
                generated_voter_private_key = data.private_key || "";

                $('.main-content').html(data.html);
                hide_loading();

                showAlert('Select a candidate. Your ECDSA digital signature will authenticate your ballot.', 'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');
            },
            error: function() {
                hide_loading();
                showAlert('Failed to load ballot.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

});
