import React from 'react';


class Search extends React.Component{
	constructor(props){
		super(props)
	}
	handleSubmit(event){
		event.preventDefault(); //prevents the page from refreshing, refresh unneeded since state update with trigger react to update dom
		console.log(this.refs);// the refs defined on inputs below.
		const email = this.refs.email.value;
		const username = this.refs.userName.value;
		const course_key = this.refs.courseKey.value;
		this.props.fetchEntitlements(email, username, course_key);
		//this.refs.commentForm.reset();
	}
	render(){
		return(
			<form ref="searchForm" className="search-form" onSubmit={this.handleSubmit.bind(this)}>
				<input type="text" ref="email" placeholder="email"/>
				<input type="text" ref="userName" placeholder="user name"/>
				<input type="text" ref="courseKey" placeholder="course key"/>
				<input type="submit" hidden/>
				<button onClick={this.handleSubmit.bind(this)}>Search</button>
			</form>
		)
	}
}


export default Search;