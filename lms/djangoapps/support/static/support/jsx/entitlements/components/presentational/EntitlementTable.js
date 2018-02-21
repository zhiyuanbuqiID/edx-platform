import React from 'react';

import { Table} from '@edx/paragon';
import { Button } from '@edx/paragon';

const entitlementColumns = [
  {
    label: 'User',
    key: 'user',
    columnSortable: true,
    onSort: () => {}
  },
  {
    label: 'Entitlement',
    key: 'uuid',
    columnSortable: true,
    onSort: () => {},
  },
  {
    label: 'Course uuid',
    key: 'course_uuid',
    columnSortable: true,
    onSort: () => {},
  },
  {
    label: 'Enrollment',
    key: 'enrollment_course_run',
    columnSortable: true,
    onSort: () => {},
  },  
  {
	  label: 'Expired At',
	  key: 'expired_at',
	  columnSortable: true,
	  onSort: () => {},
  },  
  {
	  label: 'Created',
	  key: 'created',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Modified',
	  key: 'modified',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Mode',
	  key: 'mode',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Order',
	  key: 'order_number',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
    label: 'Actions',
    key: 'button',
    columnSortable: false,
    hideHeader: false,
    onSort: () => {},
  },
];

const reissueText = "Re-issue Entitlement";


// function action(){
//   console.log('button click')
// };


// function reissueEntitlement(){
//   return <Button
//         className={['btn', 'btn-primary']}
//         label= {reissueText}
//         onClick={action.bind(this)}/>
// }

class EntitlementTable extends React.Component{
  handleReissueEntitlement(entitlement){
    console.log('button click for entitlement', entitlement)
  }
	constructor(props){
		super(props)
	}
	render(){
      console.log(this.props.entitlements)
      const entitlementData = this.props.entitlements.map((entitlement, index)=>{
      console.log('mapping button onto entitlement ', entitlement)
      return Object.assign({}, entitlement, {
        button: <Button
          className={['btn', 'btn-primary']}
          label= "Re-issue Entitlement"
          onClick={this.handleReissueEntitlement.bind(this, entitlement)}/>})
      });
		return (
			<div>
	      <Table
	        data={entitlementData}
	        columns={entitlementColumns/*this.props.entitlement_columns*/}/>
	    </div>
	   )
	}
}

export default EntitlementTable;