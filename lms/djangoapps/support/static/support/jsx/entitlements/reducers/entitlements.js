// create reducer handling 2 things
// action
// copy of current state
import ACTION_TYPES from '../actions/actionCreators';

function entitlements(state = {}, action){
	const i = action.index;
	// if action.type = ACTION_TYPES.
	console.log('entitlements reducer receiving action type:',action.type)
	switch(action.type){
		case 'FETCH_ENTITLEMENTS_REQUEST':
			console.log('fetching entitlements', action.email, action.username, action.course_key)
			return state
		case 'FETCH_ENTITLEMENTS_SUCCESS':
			console.log('Fetching entitlements success', action.error)
			return Object.assign({}, entitlement, { entitlements: action.entitlements })
		case 'FETCH_ENTITLEMENTS_FAILURE':
			console.log('Fetching entitlements failed', action.error)
			return state
		default: 
			return state;
	}
}

export default entitlements;