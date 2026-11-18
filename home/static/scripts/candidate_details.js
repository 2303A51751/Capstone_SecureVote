var current_auth_method = 'mobile';
var generated_voter_private_key = "";
var valid_email_pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Global tab switcher for voter verification methods
function switchAuthTab(method) {
    current_auth_method = method;
    if (method === 'mobile') {
        // Tab styling: Mobile Active
        $('#tab-btn-mobile').css({
            'border': '2px solid #16a34a',
            'background': '#f0fdf4',
            'color': '#15803d'
        });
        $('#tab-btn-email').css({
            'border': '2px solid #e5e7eb',
            'background': '#f9fafb',
            'color': '#6b7280'
        });
        // Panels toggle
        $('#auth-panel-mobile').show();
        $('#auth-panel-email').hide();
    } else {
        // Tab styling: Email Active
        $('#tab-btn-email').css({
            'border': '2px solid #7e22ce',
            'background': '#faf5ff',
            'color': '#7e22ce'
        });
        $('#tab-btn-mobile').css({
            'border': '2px solid #e5e7eb',
            'background': '#f9fafb',
            'color': '#6b7280'
        });
        // Panels toggle
        $('#auth-panel-email').show();
        $('#auth-panel-mobile').hide();
    }
}

$(document).ready(function(){

    // 1. Send Mobile OTP (Primary Verification Method)
    $('#send-mobile-otp').click(function(){
        var phone = $('#mobile-input').val().trim();
        if(!phone){
            showAlert('No registered phone number found.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            return;
        }

        show_loading('Dispatching SMS OTP to ' + phone + '...');

        $.ajax({
            type: 'POST',
            url: '/send-otp/',
            data: {
                'auth_method': 'mobile',
                'phone': phone
            },
            success: function(data){
                setTimeout(function(){
                    hide_loading_without_reload();
                }, 700);

                if(data.success){
                    $('#otp-destination-display').html('📱 ' + (data.destination || ('+91 ' + phone)));
                    
                    if (data.otp) {
                        $('#otp-input').val(data.otp);
                        $('#otp-demo-hint').html('Demo Mode: Mobile OTP auto-filled (' + data.otp + '). Click "Verify OTP".');
                        showAlert('Mobile OTP: ' + data.otp + ' (Auto-filled for testing)', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    } else {
                        $('#otp-input').val('').focus();
                        $('#otp-demo-hint').html('Live SMS Dispatched: Please enter the 6-digit passcode sent to your phone.');
                        showAlert('SMS OTP sent to ' + phone + '. Please check your messages!', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    }

                    $('.otp-div').removeClass('otp-verification-slide-to-bottom');
                    $('.otp-div').addClass('otp-verification-slide-from-bottom');
                    $('.otp-verification').show();
                    $('.otp-div').show();
                } else {
                    showAlert(data.error || 'Failed to dispatch Mobile OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            },
            error: function(){
                hide_loading_without_reload();
                showAlert('Network error while requesting Mobile OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

    // 2. Send Email OTP (Extra / Alternative Verification Option)
    $('#send-email-otp').click(function(){
        var email = $('#email-input').val().trim();
        if(!email || !valid_email_pattern.test(email)){
            showAlert('Please provide a valid registered email address.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            return;
        }

        show_loading('Sending OTP to ' + email + '...');

        $.ajax({
            type: 'POST',
            url: '/send-otp/',
            data: {
                'auth_method': 'email',
                'email-id': email
            },
            success: function(data){
                setTimeout(function(){
                    hide_loading_without_reload();
                }, 700);

                if(data.success){
                    $('#otp-destination-display').html('✉️ ' + (data.destination || email));
                    
                    if (data.otp) {
                        $('#otp-input').val(data.otp);
                        $('#otp-demo-hint').html('Demo Mode: Email OTP auto-filled (' + data.otp + '). Click "Verify OTP".');
                        showAlert('Email OTP: ' + data.otp + ' (Auto-filled for testing)', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    } else {
                        $('#otp-input').val('').focus();
                        $('#otp-demo-hint').html('Live Delivery: Please check registered email inbox (' + email + ') for the OTP code.');
                        showAlert('OTP sent to ' + email + '. Please check your inbox!', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    }

                    $('.otp-div').removeClass('otp-verification-slide-to-bottom');
                    $('.otp-div').addClass('otp-verification-slide-from-bottom');
                    $('.otp-verification').show();
                    $('.otp-div').show();
                } else {
                    showAlert(data.error || 'Failed to dispatch Email OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            },
            error: function(){
                hide_loading_without_reload();
                showAlert('Network error while requesting Email OTP.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

    // 3. Verify OTP
    $('#verify').click(function(){
        var code = $('#otp-input').val().trim();
        if(!code){
            showAlert('Please enter the 6-digit OTP passcode.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            return;
        }

        show_loading('Verifying cryptographic OTP passcode...');

        $.ajax({
            type: 'POST',
            url: '/verify-otp/',
            data: {'otp-input': code},
            success: function(data){
                setTimeout(function(){
                    hide_loading_without_reload();
                }, 500);

                if(data.success){
                    $('.otp-div').removeClass('otp-verification-slide-from-bottom');
                    $('.otp-div').addClass('otp-verification-slide-to-bottom');
                    setTimeout(function(){
                        $('.otp-verification').hide();
                        $('.otp-div').hide();
                    }, 400);

                    // Show verified status
                    if(data.auth_method === 'email'){
                        $('#send-email-otp').hide();
                        $('#verified-badge-email').css('display', 'inline-block');
                        $('#email-hint-msg').html('✅ <strong>Email Verified Successfully!</strong> You are authenticated.');
                        showAlert('Email Verified! You are now authorized to vote.', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    } else {
                        $('#send-mobile-otp').hide();
                        $('#verified-badge-mobile').css('display', 'inline-block');
                        $('#mobile-hint-msg').html('✅ <strong>Mobile Verified Successfully!</strong> You are authenticated.');
                        showAlert('Mobile Verified! You are now authorized to vote.', 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                    }

                    // Enable Proceed to Vote
                    $('#vote-now').removeClass('disabled');
                    $('#vote-now').css({
                        'background': '#16a34a',
                        'color': 'white',
                        'cursor': 'pointer',
                        'box-shadow': '0 4px 14px rgba(22, 163, 74, 0.4)'
                    });
                } else {
                    showAlert(data.error || 'Invalid OTP passcode.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            },
            error: function(){
                hide_loading_without_reload();
                showAlert('Verification request failed. Please retry.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

    // 4. Cancel OTP Modal
    $('#cancel-otp').click(function(){
        $('.otp-div').removeClass('otp-verification-slide-from-bottom');
        $('.otp-div').addClass('otp-verification-slide-to-bottom');
        setTimeout(function(){
            $('.otp-verification').hide();
            $('.otp-div').hide();
        }, 400);
    });

    // Support Enter in OTP input
    $('#otp-input').on('keypress', function(e){
        if(e.which === 13) {
            $('#verify').click();
        }
    });

    // 5. Proceed to Vote
    $('#vote-now').click(function(event){
        if($(this).hasClass('disabled')) return;

        show_loading('Generating NIST P-256 Elliptic Curve Keypair & Ballot...');

        $.ajax({
            type: 'GET',
            url: '/get-parties/',
            success: function(data){
                if (data.error) {
                    hide_loading();
                    showAlert(data.error, 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                    return;
                }

                parties_list_json = data.parties;
                generated_voter_private_key = data.private_key || "";

                $('.main-content').html(data.html);
                hide_loading();

                showAlert('Select a candidate. Your NIST P-256 digital signature will seal your ballot.', 'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');
            },
            error: function() {
                hide_loading();
                showAlert('Failed to load ballot.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        });
    });

});
