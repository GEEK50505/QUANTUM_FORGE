import http from 'http';

http.get('http://localhost:5173/', (res) => {
  console.log('STATUS', res.statusCode);
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    console.log(data.slice(0, 1000));
  });
}).on('error', (e) => console.error('ERR', e));
