$(document).ready(function () {
    hide_loading();
    showAlert(
        'Welcome! Enter your Aadhaar number or select a demo voter below to begin.',
        'rgba(201, 136, 255, 0.3)', 'rgb(102, 0, 128)');

    setTimeout(function () {
        $('.loading-div').css({
            'height': 'calc(100vh - 50px)',
            'top': '50px',
        });
    }, 1000);

    // Support Enter key on input
    $('#aadhar').on('keypress', function (e) {
        if (e.which === 13) {
            submit_aadhar();
        }
    });

    // Load live sample voters from server
    loadSampleVoters();
});

// Select a demo voter
function selectDemoVoter(uuid) {
    $('#aadhar').val(uuid);
    $('#auth-inline-msg').hide();
    submit_aadhar();
}

// Reset a voter so the user can test again immediately
function resetDemoVoter(uuid) {
    show_loading('Resetting voting status for voter...');
    $.ajax({
        type: 'POST',
        url: '/reset-voter/',
        data: {'uuid': uuid},
        success: function(resp) {
            hide_loading();
            if(resp.success) {
                showAlert(resp.message, 'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
                $('#auth-inline-msg').hide();
                $('#aadhar').val(uuid);
                loadSampleVoters();
                submit_aadhar();
            } else {
                showAlert(resp.error, 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            }
        },
        error: function() {
            hide_loading();
            showAlert('Failed to reset voter.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
        }
    });
}

function loadSampleVoters() {
    $.ajax({
        type: 'GET',
        url: '/api/sample-voters/',
        success: function (data) {
            if (data.unvoted && data.unvoted.length > 0) {
                var readyHtml = '';
                for (var v of data.unvoted) {
                    var emailTag = v.email ? ' • ' + v.email : '';
                    readyHtml += '<span class="demo-chip ready" onclick="selectDemoVoter(\'' + v.uuid + '\')">' +
                        '<strong>' + v.name + '</strong> (' + formatAadhaar(v.uuid) + ')' + emailTag + '</span>';
                }
                $('#ready-voters').html(readyHtml);
            }
            if (data.voted && data.voted.length > 0) {
                var votedHtml = '';
                for (var v of data.voted) {
                    var emailTag = v.email ? ' • ' + v.email : '';
                    votedHtml += '<span class="demo-chip voted" onclick="selectDemoVoter(\'' + v.uuid + '\')">' +
                        '<strong>' + v.name + '</strong> (' + formatAadhaar(v.uuid) + ')' + emailTag + ' - Voted</span>';
                }
                $('#voted-voters').html(votedHtml);
                $('#voted-group').show();
            } else {
                $('#voted-group').hide();
            }
        }
    });
}

function formatAadhaar(val) {
    var digits = ('' + val).replace(/\D/g, '');
    if (digits.length === 12) {
        return digits.substring(0, 4) + ' ' + digits.substring(4, 8) + ' ' + digits.substring(8, 12);
    }
    return val;
}

// Aadhar input formatting
$('#aadhar').on('input', function () {
    $('#auth-inline-msg').hide();
    var raw = $(this).val().replace(/\D/g, '');
    if (raw.length > 12) {
        raw = raw.substring(0, 12);
    }
    if (raw.length > 8) {
        $(this).val(raw.substring(0, 4) + ' ' + raw.substring(4, 8) + ' ' + raw.substring(8));
    } else if (raw.length > 4) {
        $(this).val(raw.substring(0, 4) + ' ' + raw.substring(4));
    } else {
        $(this).val(raw);
    }
});

// Authenticate aadhar no after button click
function submit_aadhar() {
    var aadhar_raw = $('#aadhar').val().replace(/\s+/g, '').replace(/-/g, '');
    if (!aadhar_raw) {
        showInlineError('Please enter an Aadhaar card number.');
        showAlert('Please enter an Aadhaar card number.', 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
        return;
    }

    show_loading('Authenticating identity with Electoral Registry...');
    $('#auth-inline-msg').hide();

    function handleAuthSuccess(data) {
        if (data.success) {
            candidate_details_json = data.details;

            showAlert(
                'Identity Authenticated! Proceed to email OTP verification.',
                'rgba(136, 255, 156, 0.3)', 'rgb(0, 128, 0)');
            
            $('.main-content').html(data.html);
            hide_loading();
            showShortDetails();
        } else {
            hide_loading();
            showAlert(data.error, 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
            
            if (data.already_voted) {
                var resetBtnHtml = '<div style="margin-top: 8px;">' +
                    '<button type="button" onclick="resetDemoVoter(\'' + (data.voter_uuid || aadhar_raw) + '\')" ' +
                    'style="background: #7e22ce; color: white; border: none; padding: 6px 14px; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: bold;">' +
                    '🔄 Reset Vote Status (Allow Re-Testing)' +
                    '</button></div>';
                showInlineError('⚠️ ' + data.error + resetBtnHtml);
            } else {
                showInlineError('⚠️ ' + data.error);
            }
        }
    }

    // Try POST first
    $.ajax({
        type: "POST",
        url: "/authentication/",
        data: {'aadhar_no': aadhar_raw},
        success: handleAuthSuccess,
        error: function (xhr, status, err) {
            // Fallback to GET if POST is blocked by proxy or CSRF
            $.ajax({
                type: "GET",
                url: "/authentication/",
                data: {'aadhar_no': aadhar_raw},
                success: handleAuthSuccess,
                error: function(xhr2, status2, err2) {
                    hide_loading();
                    var msg = 'Authentication request failed (' + (err2 || err || 'Network Error') + ').';
                    showInlineError(msg);
                    showAlert(msg, 'rgba(255, 82, 82, 0.3)', 'rgb(122, 0, 0)', 'vibrate');
                }
            });
        }
    });
}

function showInlineError(msg) {
    $('#auth-inline-msg').css({
        'background': '#fef2f2',
        'border': '1px solid #fca5a5',
        'color': '#991b1b',
        'display': 'block'
    }).html(msg);
}

// Show short Details at top right corner after authentication
function showShortDetails() {
    if (candidate_details_json) {
        $('.basic-details').html(candidate_details_json.uuid + ' (' + candidate_details_json.name + ')');
        $('.profile-pic').first().attr('src', candidate_details_json.profile_pic || '/static/images/profile-bg.png');
        $('.short-details').css('display', 'flex');
    }
}
