// Sample JavaScript file for testing GritQL patterns
function hello(name) {
  console.log("Hello, " + name);
  var message = "Welcome!";
  console.log(message);
}

function goodbye(name) {
  console.log("Goodbye, " + name);
  var farewell = "See you later!";
  console.log(farewell);
}

// React-like component
function MyComponent(props) {
  return <div>Hello {props.name}</div>;
}