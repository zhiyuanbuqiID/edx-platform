import ACTION_TYPES from '../actions/actionCreators';

function modal(state = {}, action){
	const i = action.index;
	// if action.type = ACTION_TYPES.
	console.log('entitlements reducer receiving action type:',action.type)
	switch(action.type){
		case 'OPEN_REISSUE_MODAL':
			console.log('OPEN_REISSUE_MODAL reduce for entitlement',action.entitlement )
			return state
		case 'OPEN_CREATION_MODAL':
			console.log('OPEN_CREATION_MODAL reduce')
			return state
		case 'CLOSE_MODAL':
			console.log('CLOSE_MODAL reduce')
			return clearModal();
		case 'UPDATE_ENTITLEMENT_SUCCESS':
			return clearModal();
		case 'CREATE_ENTITLEMENT_SUCCESS':
			return clearModal();
		default: 
			return state;
	}
}

function clearModal(state){
	return Object.assign({}, state, {modalOpen:false, activeEntitlement:{}}
}

export default modal;