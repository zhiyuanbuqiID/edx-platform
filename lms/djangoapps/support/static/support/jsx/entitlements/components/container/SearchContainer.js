import { connect } from 'react-redux';

import * as actionCreators from '../../actions/actionCreators';
import Search from '../presentational/Search';

const mapStateToProps = (state) => {
  return {
    entitlements: state.entitlements
  };
}

const mapDispatchToProps = (dispatch) => {
  return {
    fetchEntitlements: (email,username,course_key) => {
      dispatch(actionCreators.fetchEntitlements(email,username,course_key));
    }
  };
}

const SearchContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Search);

export default SearchContainer;
