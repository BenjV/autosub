
$(document).ready(function () {
    $('#wanted').dataTable({
        "deferRender": true,
        "orderClasses": true,
        "stateSave": true,
        "iCookieDuration": 32000000,
        "stateDuration": -1,
        "lengthMenu": [ [5, 10, 25, 50, 100, -1],[5, 10, 25, 50, 100, "All"] ],
        "order": [[4, "asc"]],
        "columnDefs": [
            {"orderData": [3, 4], "targets": [3] },
            {"orderData": [0, 1, 2], "targets": [0] },
            {"orderable": false, "targets": [5, 11, 12]}
        ],
    });

    $('#downloaded').dataTable({
        "deferRender": true,
        "orderClasses": true,
        "stateSave": true,
        "iCookieDuration": 32000000,
        "stateDuration": -1,
        "lengthMenu": [ [5, 10, 25, 50, 100, -1], [5, 10, 25, 50, 100, "All"] ],
        "order": [[3, "desc"]],
        "columnDefs": [
            { "orderData": [0, 1, 2], "targets": [0] },
            { "orderable": false, "targets": 10 }
        ]
    });

    $('#testMail').click(function () {
        $('#testMail-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Mail...</span>');
        var mailsrv = $("#mailsrv").val();
        var mailfromaddr = $("#mailfromaddr").val();
        var mailtoaddr = $("#mailtoaddr").val();
        var mailusername = $("#mailusername").val();
        var mailpassword = $("#mailpassword").val();
        var mailsubject = $("#mailsubject").val();
        var mailencryption = $("#mailencryption").val();
        var mailauth = $("#mailauth").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testMail", {
            'mailsrv': mailsrv,
            'mailfromaddr': mailfromaddr,
            'mailtoaddr': mailtoaddr,
            'mailusername': mailusername,
            'mailpassword': mailpassword,
            'mailsubject': mailsubject,
            'mailencryption': mailencryption,
            'mailauth': mailauth,
            'dummy': dummy
        },
            function (data) {
                $('#testMail-result').html(data);
            });
    });

    $('#testTwitter').click(function () {
        $('#testTwitter-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Twitter...</span>');
        var twitterkey = $("#twitterkey").val();
        var twittersecret = $("#twittersecret").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testTwitter", {
            'twitterkey': twitterkey,
            'twittersecret': twittersecret,
            'dummy': dummy
        },
            function (data) {
                $('#testTwitter-result').html(data);
            });
    });

    $('#testPushalot').click(function () {
        $('#testPushalot-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Pushalot...</span>');
        var pushalotapi = $("#pushalotapi").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testPushalot", {
            'pushalotapi': pushalotapi,
            'dummy': dummy
        },
            function (data) {
                $('#testPushalot-result').html(data);
            });
    });

    $('#testPushbullet').click(function () {
        $('#testPushbullet-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Pushbullet...</span>');
        var pushbulletapi = $("#pushbulletapi").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testPushbullet", {
            'pushbulletapi': pushbulletapi,
            'dummy': dummy
        },
            function (data) {
                $('#testPushbullet-result').html(data);
            });
    });

    $('#testNotifyMyAndroid').click(function () {
        $('#testNotifyMyAndroid-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Notify My Android...</span>');
        var nmaapi = $("#nmaapi").val();
        var nmapriority = $("#nmapriority").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testNotifyMyAndroid", {
            'nmaapi': nmaapi,
            'nmapriority': nmapriority,
            'dummy': dummy
        },
            function (data) {
                $('#testNotifyMyAndroid-result').html(data);
            });
    });

    $('#testPushover').click(function () {
        $('#testPushover-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Pushover...</span>');
        var pushoverappkey = $("#pushoverappkey").val();
        var pushoveruserkey = $("#pushoveruserkey").val();
        var pushoverpriority = $("#pushoverpriority").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testPushover", {
            'pushoverappkey': pushoverappkey,
            'pushoveruserkey': pushoveruserkey,
            'pushoverpriority': pushoverpriority,
            'dummy': dummy
        },
            function (data) {
                $('#testPushover-result').html(data);
            });
    });

    $('#testGrowl').click(function () {
        $('#testGrowl-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Growl...</span>');
        var growlhost = $("#growlhost").val();
        var growlport = $("#growlport").val();
        var growlpass = $("#growlpass").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testGrowl", {
            'growlhost': growlhost,
            'growlport': growlport,
            'growlpass': growlpass,
            'dummy': dummy
        },
            function (data) {
                $('#testGrowl-result').html(data);
            });
    });

    $('#testProwl').click(function () {
        $('#testProwl-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Prowl...</span>');
        var prowlapi = $("#prowlapi").val();
        var prowlpriority = $("#prowlpriority").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testProwl", {
            'prowlapi': prowlapi,
            'prowlpriority': prowlpriority,
            'dummy': dummy
        },
            function (data) {
                $('#testProwl-result').html(data);
            });
    });

    $('#testTelegram').click(function () {
        $('#testTelegram-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Telegram...</span>');
        var telegramapi = $("#telegramapi").val();
        var telegramid = $("#telegramid").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testTelegram", {
            'telegramapi': telegramapi,
            'telegramid': telegramid,
            'dummy': dummy
        },
            function (data) {
                $('#testTelegram-result').html(data);
            });
    });

    $('#testBoxcar2').click(function () {
        $('#testBoxcar2-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Boxcar2...</span>');
        var boxcar2token = $("#boxcar2token").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testBoxcar2", {
            'boxcar2token': boxcar2token,
            'dummy': dummy
        },
            function (data) {
                $('#testBoxcar2-result').html(data);
            });
    });

    $('#testPlex').click(function () {
        $('#testPlex-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Plex Media Server...</span>');
        var plexserverhost = $("#plexserverhost").val();
        var plexserverport = $("#plexserverport").val();
        var plexserverusername = $("#plexserverusername").val();
        var plexserverpassword = $("#plexserverpassword").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testPlex", {
            'plexserverhost': plexserverhost,
            'plexserverport': plexserverport,
            'plexserverusername': plexserverusername,
            'plexserverpassword': plexserverpassword,
            'dummy': dummy
        },
            function (data) {
                $('#testPlex-result').html(data);
            });
    });

    $('#testKodi').click(function () {
        $('#testKodi-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Kodi Media Server...</span>');
        var kodiserverhost = $("#kodiserverhost").val();
        var kodiserverport = $("#kodiserverport").val();
        var kodiserverusername = $("#kodiserverusername").val();
        var kodiserverpassword = $("#kodiserverpassword").val();
        var dummy = Date.now();
        $.get(autosubRoot + "/config/testKodi", {
            'kodiserverhost': kodiserverhost,
            'kodiserverport': kodiserverport,
            'kodiserverusername': kodiserverusername,
            'kodiserverpassword': kodiserverpassword,
            'dummy': dummy
        },
        function (data) {
            $('#testKodi-result').html(data);
        });
    });

    $('#verifyTvdb').click(function () {
        $('#verifyTvdb-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Verifying...</span>');
        $.get(autosubRoot + "/config/verifyTvdb", {
            'tvdbuser': $("#tvdbuser").val(),
            'tvdbaccountid': $("#tvdbaccountid").val(),
            'dummy': Date.now()
        },
            function (data) {
                $('#verifyTvdb-result').html(data);
            });
    });

    $('#testAddic7ed').click(function () {
        $('#testAddic7ed-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing Addic7ed login...</span>');
        $.get(autosubRoot + "/config/testAddic7ed", {
            'addic7eduser': $("#addic7eduser").val(),
            'addic7edpasswd': $("#addic7edpasswd").val(),
            'dummy': Date.now()
        },
        function (data) {
             $('#testAddic7ed-result').html(data);
        });
    });

    $('#testOpenSubtitles').click(function () {
        $('#testOpenSubtitles-result').html('<span><img src="' + autosubRoot + '/images/loading16.gif"> Testing OpenSubtitles login...</span>');
        $.get(autosubRoot + "/config/testOpenSubtitles", {
            'opensubtitlesuser': $("#opensubtitlesuser").val(),
            'opensubtitlespasswd': $("#opensubtitlespasswd").val(),
            'dummy': Date.now()
        },
        function (data) {
            $('#testOpenSubtitles-result').html(data);
        });
    });

    // Code to display the tooltip and popover.
    $("a").tooltip();
    $("span").popover();

    $("span").on('shown.bs.popover', function () {
        $("span").not(this).popover('hide');
    });

    // Code to hide/show the notification fields.
    $(".enabler option:selected").each(function () {
        if ($(this).val() == "False") {
            $('#content_' + $(this).parent().attr("id")).hide();
        }
    });

    $(".enabler").change(function () {
        var dropdown = $(this);
        $(this).children("option:selected").each(function () {
            if ($(this).val() == "True") {
                $('#content_' + dropdown.attr("id")).show();
            }
            if ($(this).val() == "False") {
                $('#content_' + dropdown.attr("id")).hide();
            }
        });
    });  
});

