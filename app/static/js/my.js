// click on menu's basic information
function func_my_basic_info() {
    $('#my_basic_info').addClass('list-group-item-info');
    $('#my_basic_setting').removeClass('list-group-item-info');
    $('#my_help').removeClass('list-group-item-info');
    $('#my_images').removeClass('list-group-item-info');
    $('#image-pagination').html('');

    $("#main-body").load("my_basic_info");
}

// click on menu's basic setting
function func_my_basic_setting() {
    $('#my_basic_setting').addClass('list-group-item-info');
    $('#my_basic_info').removeClass('list-group-item-info');
    $('#my_help').removeClass('list-group-item-info');
    $('#my_images').removeClass('list-group-item-info');
    $('#image-pagination').html('');

    $.get("my_basic_setting", function(data) {
        $('#main-body').html(data);
    });
}

// click on basic setting's save button
function func_save_setting() {
    var is_have_account = $('input[name="is_have_account"]:checked').val();
    var access_key_value = $('#access_key').val();
    var secret_key_value = $('#secret_key').val();
    var bucket_name_value = $('#bucket_name').val();
    var domain_value = $('#domain').val();

    var post_data = {
        'is_have_account': is_have_account,
        'access_key': access_key_value,
        'secret_key': secret_key_value,
        'bucket_name': bucket_name_value,
        'domain': domain_value
    };
    $.post('/my_basic_setting', post_data, function(data) {
        $('#return-result').html(data);
    });
}

// click on menu's help
function func_my_help() {
    $('#my_help').addClass('list-group-item-info');
    $('#my_basic_info').removeClass('list-group-item-info');
    $('#my_basic_setting').removeClass('list-group-item-info');
    $('#my_images').removeClass('list-group-item-info');
    $('#image-pagination').html('');

    $("#main-body").load("my_help");
}

// click on menu's image manage
var g_back_page = 1;
function func_my_images() {
    $('#my_basic_info').removeClass('list-group-item-info');
    $('#my_basic_setting').removeClass('list-group-item-info');
    $('#my_help').removeClass('list-group-item-info');
    $('#my_images').addClass('list-group-item-info');
    $('#image-pagination').html('');

    var current_page = 1;
    make_pagination(current_page);

    $("#main-body").load('my_images/1');
}

// create pagination
function make_pagination(current_page_param) {
    $.get("api/get_all_images_count", function (data) {

        var current_page = current_page_param;
        var total_images = data;
        var total_pages = Math.ceil(total_images/5);
        if (total_pages == 0) {
            total_pages += 1;
        }

        var page_bar = '<ul class="pagination">';
        page_bar += '<li><a style="outline: none" href="#" id="prev" role="button" class="btn" ' +
            'onclick="prev_page('+current_page+')">上一页</a></li>';
        page_bar += '<li><a id="page">' + current_page + '/' + total_pages+'</a></li>';
        page_bar += '<li><a style="outline: none;" href="#" id="next" role="button" class="btn" ' +
            'onclick="next_page('+current_page+','+total_pages+')">下一页</a></li>';
        page_bar += '</ul>';
        $('#image-pagination').html(page_bar);
        if (current_page == 1) {
            $("#prev").addClass('disabled');
        }
        if (current_page >= total_pages) {
            $("#next").addClass('disabled');
        }
    });
}

// click prev button
function prev_page(current_page_param) {
    var current_page = current_page_param;
    if (current_page <= 1) {
        $("#main-body").load('my_images/1');
    } else {
        $("#main-body").load('my_images/'+(current_page-1));
    }
    make_pagination(current_page-1);
    g_back_page -= 1;
}

// click next button
function next_page(current_page_param, total_pages_param) {
    var current_page = current_page_param;
    var total_pages = total_pages_param;
    if (current_page >= total_pages) {
        $("#main-body").load('my_images/1');
    } else {
        $("#main-body").load('my_images/'+(current_page+1));
    }
    make_pagination(current_page+1);
    g_back_page += 1;
}

// click details information and edit information
function func_edit_image(image_id_param) {
    var image_id = image_id_param;
    $("#image-pagination").html('');
    $("#main-body").load('my_edit_image/'+image_id);
}

// back to image list
function func_back_to_list() {
    $("#main-body").load('my_images/'+g_back_page);
    make_pagination(g_back_page);
}

// edit on save
function func_save_edit(image_id_param) {
    var title_value = $("#title").val();
    var description_value = $("#description").val();
    var image_id_value = image_id_param;

    var post_data = {
        'title': title_value,
        'description': description_value,
        'image_id': image_id_value
    };

    $.post('/my_edit_image_save', post_data, function(data) {
        $('#edit-save-result').html(data);
    });

}

$(document).ready(function() {
    // send a click to basic info
    $('#my_basic_info').click();
});

