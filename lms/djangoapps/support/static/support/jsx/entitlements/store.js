import { createStore, compose, applyMiddleware } from 'redux';
//import { syncHistoryWithStore } from 'react-router-redux';
//import { browserHistory } from 'react-router';
import thunkMiddleware from "redux-thunk"; 

// import root reducer
import rootReducer from './reducers/index';

import entitlements from './data/entitlements';



const initial_entitlements = []//entitlements;

//create default data
const defaultState = {
	entitlements: initial_entitlements,
	modalOpen: true
}

// const enhancers = compose(
// 	window.devToolsExtension ? window.devToolsExtension() : f=>f
//);


// const createStoreWithMiddleware = compose(  
//   applyMiddleware(thunkMiddleware)
// )(createStore);

function configureStore(initialState){//, enhancers) {  
  // const store = createStoreWithMiddleware(rootReducer, defaultState, enhancers);
  return createStore(
    rootReducer,
    initialState,
    applyMiddleware(thunkMiddleware),
    //enhancers
  );
  // return store;
}
const store = configureStore(defaultState);//, enhancers);


//export const history = syncHistoryWithStore(browserHistory, store);

// if(module.hot){
// 	module.hot.accept('./reducers/',()=>{
// 		const nextRootReducer = require('./reducers/index').default;
// 		store.replaceReducer(nextRootReducer);
// 	});
//}

export default store;