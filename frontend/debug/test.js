import axios from 'axios';
axios.get('http://127.0.0.1:8000/posts/?page=0&page_size=10').then(res => {
  console.log("Success", res.data);
}).catch(err => {
  console.log("Error", err.message);
});
