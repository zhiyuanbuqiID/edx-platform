import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import * as actionCreators from '../../actions/actionCreators';
import EntitlementModal from '../presentational/Search';

const mapStateToProps = (state) => {
  return {
    modalEntitlement: state.modalEntitlement,
    modalOpen: state.modalOpen
  };
}

const mapDispatchToProps = (dispatch) => {
  return bindActionCreators(actionCreators, dispatch);
  // return {
  //   fetchEntitlements: (email,username,course_key) => {
  //     dispatch(actionCreators.fetchEntitlements(email,username,course_key));
  //   }
  // };
}

const EntitlementModalContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(EntitlementModal);

export default EntitlementModalContainer;