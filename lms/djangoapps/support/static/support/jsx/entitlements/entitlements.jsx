// let's go!
import React from 'react';
import {render} from 'react-dom';

//Import css
//import css from './styles/style.styl';

//Import components
import App from './components/container/App';
import SearchContainer from './components/container/SearchContainer';
//import EntitlementList from './components/presentational/EntitlementList';
import EntitlementTable from './components/presentational/EntitlementTable';

//Import React Router dependecies
//import {Router, Route, IndexRoute, browserHistory } from 'react-router';
import {Provider } from 'react-redux';

import store, {history} from './store';

export class EntitlementSupportPage extends React.Component {
	render(){
		return	(
			<Provider store={store} >
				<App>
					{/*<EntitlementList/>*/}
					<EntitlementTable/>
				</App>
				{/*
				<Router history={history}>
					<Route path = "/" component = {App}>
						<IndexRoute component={EntitlementTable}> </IndexRoute>
						<Route path = "/view/:entitlement_uuid" component = {Single}></Route>
					</Route>
				</Router>
				*/}
			</Provider>
		)
	}
}

//render(router, document.getElementById('root')); 