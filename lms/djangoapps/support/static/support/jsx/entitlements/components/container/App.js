import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import * as actionCreators from '../../actions/actionCreators';
import Main from '../presentational/Main';

function mapStateToProps(state){
	console.log('mapping state to props', state)
	return{
		entitlements: state.entitlements,
		modalOpen: state.modalOpen
	}
}

function mapDispatchToProps(dispatch){
	console.log('mapping dispatch to props')
	return bindActionCreators(actionCreators, dispatch);
}

const App = connect(mapStateToProps,
	mapDispatchToProps)(Main);//takes all the props and data from state and dispatch and maps them to main.



export default App;