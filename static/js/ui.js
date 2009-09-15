
// Simple JavaScript Templating
// John Resig - http://ejohn.org/ - MIT Licensed
// via: http://ejohn.org/blog/javascript-micro-templating
(function(){
  var cache = {};
 
  this.tmpl = function tmpl(str, data){
    // Figure out if we're getting a template, or if we need to
    // load the template - and be sure to cache the result.
    var fn = !/\W/.test(str) ?
      cache[str] = cache[str] ||
        tmpl(document.getElementById(str).innerHTML) :
     
      // Generate a reusable function that will serve as a template
      // generator (and which will be cached).
      new Function("obj",
        "var p=[],print=function(){p.push.apply(p,arguments);};" +
       
        // Introduce the data as local variables using with(){}
        "with(obj){p.push('" +
       
        // Convert the template into pure JavaScript
        str
          .replace(/[\r\t\n]/g, " ")
          .split("<%").join("\t")
          .replace(/((^|%>)[^\t]*)'/g, "$1\r")
          .replace(/\t=(.*?)%>/g, "',$1,'")
          .split("\t").join("');")
          .split("%>").join("p.push('")
          .split("\r").join("\\'")
      + "');}return p.join('');");
   
    // Provide some basic currying to the user
    return data ? fn( data ) : fn;
  };
})();

$.postJSON = function(url, data, callback) {
    $.post(url, data, callback, "json");
};

function _handle_delete(){
    $('.delete').live('click', function() {
        if (!confirm('Are you sure you want to delete this entry?')) {
            return false
        } 
        var entry = $(this).parents('.post');
        $.getJSON('/delete/'+entry.attr('id'), function(data) {
            if (data.success) {
                entry.slideUp();
            }
        });
        return false;
    });
};

function _handle_pre_edit(){
    $('.edit').live('click', function() {
        var entry = $(this).parents('.post');
        var key = entry.attr('id');
        var body = $('#b-'+key).html();
        var linkelt = $('#l-'+key);
        if (linkelt.length > 0) 
            link=linkelt.attr('href'); 
        else
            link = '';
        entry_html = entry.html();
        editform = tmpl('postform_tmpl', {'key':key, 'body':body, 'link':link, 'entry_html':entry_html});
        entry.html(editform);
        return false;
    });
    $('.cancel').live('click', function(){
        var entry = $(this).parents('.post');
        var key = entry.attr('id');
        tmp_entry = $('#tmp-'+key).html();
        entry.html(tmp_entry);
        return false;
    });
};

function _handle_edit(){
    $('.editform').live('submit',function(){
        var key = $(this).attr('id').replace('f-', '');
        var body = $('#fb-'+key).val();
        var link = $('#fl-'+key).val();
        var entry = $('#'+key);
        if ($.trim(body) == ''){
            alert('You should type a message! The link is optional');
        }
        else{
            $.postJSON("/edit/"+key, {body:body, link:link}, function(data){
                //use your template baka! - now back to honey and clover
                //alert('saved: '+body+' '+link);
                var htmlpost = tmpl('post_tmpl', data);
                entry.html(htmlpost);
                }
            );
        }
        return false;
    });
};

function _toggle_share_form(){
    $('#toggleshareform').click(
        function(){
            $('#body').val('');
            $('#link').val('');
            $('#sharediv').slideToggle()        
        }
    );
};

function _insert_entry(data){
    entry = data;
    var htmlpost = tmpl('post_tmpl', entry)
    div = document.createElement('div')
    $(div).addClass('post').attr('id', entry['key']);
    $(div).html(htmlpost);
    $("#entries").prepend(div)
};

function _ajax_share(){
    $('#shareform').submit(function(){
            var body = $('#body').val();
            var link = $('#link').val();
            if ($.trim(body) == ''){
                alert('You should type a message! The link is optional');
            }
            else{
                $.postJSON("/create", {body:body, link:link}, function(data){
                        _insert_entry(data);
                        $('#sharediv').slideToggle();
                });
            }
            return false;
    });
};

function _update_view(URL){
    $.getJSON(URL, function(data){
        entries = data['entries'];
        for (i=0; i < entries.length ; i++){
            e = entries[i];
            key = e['key'];
            //improve with edited entries: compare updated dates
            if ($('#'+key).length == 0)
                _insert_entry(e);
        }
    });
};

function _make_it_nicer(){
    DD_roundies.addRule('#toggleshareform', 25);
    DD_roundies.addRule('.post', 4);
}

$(document).ready(function() {
    _make_it_nicer();
    _toggle_share_form();
    _ajax_share();
    _handle_delete();
    _handle_pre_edit();
    _handle_edit();
});

