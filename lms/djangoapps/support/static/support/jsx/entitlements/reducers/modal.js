import ACTION_TYPES from '../actions/actionCreators';

function modal(state = {}, action){
	const i = action.index;
	// if action.type = ACTION_TYPES.
	console.log('entitlements reducer receiving action type:',action.type)
	switch(action.type){
		case 'OPEN_REISSUE_MODAL':
			console.log('OPEN_REISSUE_MODAL reduce for entitlement', action.entitlement)
			return state
		case 'CLOSE_REISSUE_MODAL':
			console.log('CLOSE_REISSUE_MODAL reduce')
			return state
		case 'OPEN_CREATION_MODAL':
			console.log('OPEN_CREATION_MODAL reduce')
			return state
		case 'CLOSE_CREATION_MODAL':
			console.log('CLOSE_CREATION_MODAL reduce')
			return state
		default: 
			return state;
	}
}

export default modal;