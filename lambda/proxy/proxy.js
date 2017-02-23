'use strict';

var http = require('http');

exports.handler = function(event, context) {

  // Setup request options and parameters
  var options = {
    host: process.env.UPSTREAM_HOST,
    port: 80,
    path: event.path,
    method: event.httpMethod
  };

  // If you have headers, set them. Otherwise set to an empty map.
  if (event.headers && Object.keys(event.headers).length > 0) {
    options.headers = event.headers
  } else {
    options.headers = {};
  }

  // Build the query string.
  if ( event.queryStringParameters && event.queryStringParameters && Object.keys(event.queryStringParameters).length > 0 ) {
    var queryString = generateQueryString(event.queryStringParameters);
    if (queryString !== '') {
      options.path += '?' + queryString;
    }
  }

  var req = http.request(options, function(response) {
    var responseString = '';
    response.setEncoding('utf8');

    // Another chunk of data has been received, so append it to `str`.
    response.on('data', function (chunk) {
      responseString += chunk;
    });

    // The whole response has been received
    response.on('end', function () {
      var result = {
        statusCode: response.statusCode,
        headers: response.headers,
        body: responseString
      };
      context.succeed(result);
    })

  });

  if (event.body && event.body !== '') {
    req.write(event.body);
  }

  req.on('error', function(e) {
    console.log('problem with request: ' + e.message);
    context.fail({statusCode: 500, headers: {}, body: e.message});
  });

  req.end();
};

function generateQueryString(params) {
  var str = [];
  for(var p in params) {
    if (params.hasOwnProperty(p)) {
      str.push(encodeURIComponent(p) + '=' + encodeURIComponent(params[p]));
    }
  }
  return str.join('&');
}
